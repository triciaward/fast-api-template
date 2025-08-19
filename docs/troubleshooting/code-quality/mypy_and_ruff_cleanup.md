# mypy and ruff cleanup guide (Template‑focused)

This guide applies to the FastAPI Template repository itself (not downstream apps). It explains why type-checking issues happen, how to interpret them, and a practical plan to keep the template lint/type‑clean so new projects start from a solid baseline.

## Scope and goals
- Applies to the template code under `app/**` and `tests/**` in this repo.
- Goal: clean Ruff, green tests, and a quiet mypy baseline with minimal, intentional overrides.

## Why mypy can complain in this template
- Strict config: `disallow_untyped_defs`, `disallow_untyped_decorators`, `warn_unused_ignores`, `warn_unreachable` expose missing annotations, decorator typing, unused ignores, and dead code.
- SQLAlchemy typing: classic `Column[...]` style models are fine, but stricter typing prefers SQLAlchemy 2.x `Mapped[...]`/`mapped_column`. Mixed patterns can confuse mypy.
- Decorators: Celery task decorators make functions “untyped” under `disallow_untyped_decorators`.
- Legacy or broad `# type: ignore`: often unnecessary → flagged as unused.
- Pydantic vs ORM: building Pydantic responses from ORM attributes may add ignores if types are too loose.
- Third‑party stubs: `psutil` is used in `app/api/system/health.py`; Celery and `authlib` can surface typing gaps depending on versions.

## Template baselines and small config adjustments
- Keep Ruff/Black standard. Use the loop below to verify locally.
- Add minimal mypy overrides that match the template:
  - Prefer installing `types-psutil`. If not, add an override:
    ```toml
    [[tool.mypy.overrides]]
    module = ["psutil"]
    ignore_missing_imports = true
    ```
  - Silence Celery decorator noise without weakening the whole codebase:
    ```toml
    [[tool.mypy.overrides]]
    module = ["app.services.background.celery_tasks"]
    disallow_untyped_decorators = false
    ```
  - Only add `authlib.*` ignores if mypy actually flags them in your environment.

## Low‑risk code improvements to keep the template clean
- Endpoints and services: add explicit return types where obvious (dicts/booleans/strings) and remove unused `# type: ignore`.
- Redis service (`app/services/external/redis.py`): keep `None` guards before `ping()` and prefer explicit types for the client; avoid broad ignores.
- Database module (`app/database/database.py`): keep `AsyncSession` return types on dependencies; avoid unused ignores.
- Health endpoints (`app/api/system/health.py`): type response dicts and make Redis checks conditional; document `psutil` typing approach.
- Error handling (`app/core/error_handling/error_handlers.py`): normalize `HTTPException.detail` handling so unions don’t leak `Any`.
- Security helpers (`app/core/security/security.py`): ensure functions return concrete `str`/`bool`.
- OAuth service (`app/services/auth/oauth.py`): cast JSON responses to concrete types and annotate returns.
- Middleware rate limiter (`app/services/middleware/rate_limiter.py`): ensure wrapper generics/return types are concrete (avoid `Any`).
- Models: leave classic `Column[...]` or incrementally migrate to `Mapped[...]`/`mapped_column` (see below). Keep `__repr__` and simple boolean helpers typed.

## Optional: SQLAlchemy 2.0 typing patterns
If you want maximum type safety, migrate models to `Mapped[...]` and `mapped_column` and type relationships explicitly. Avoid assigning to `Column[...]` descriptors in instance methods; mutate instance attributes instead. Consider this for:
- `app/models/auth/user.py`
- `app/models/auth/refresh_token.py`
- `app/models/auth/api_key.py`
- `app/models/system/audit_log.py`

This migration is optional; the template works with classic `Column` declarations. Do it incrementally to avoid churn.

## Forward references in models
When adding relationship type hints, guard imports and use string annotations:
```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.auth.user import User

user: "User"
```

## Decorator‑heavy modules (Celery)
For `app/services/background/celery_tasks.py`, prefer a mypy override (`disallow_untyped_decorators = false`). Alternatively, add typed wrappers with `ParamSpec`/`TypeVar`, but the override is simpler and localized.

## API schemas vs ORM data
Replace ignores by either tightening model field types or mapping ORM objects to schema‑ready dicts before instantiating Pydantic models. Narrow `Optional` values before calling CRUD so mypy sees non‑optional inputs.

## Test tip: AsyncMock
When patching async functions, use `new_callable=AsyncMock` and ensure the call site awaits the function.

## Recommended working loop
```bash
ruff check
mypy --config-file pyproject.toml
pytest -q
```
Commit in small chunks.

## Template cleanup checklist (action plan)
- [ ] Add mypy override for `psutil` or install `types-psutil` and remove the override
- [ ] Add mypy override for `app.services.background.celery_tasks` (`disallow_untyped_decorators = false`)
- [ ] `app/api/system/health.py`: ensure typed return dicts; keep Redis conditional checks; document psutil typing
- [ ] `app/services/external/redis.py`: remove broad `type: ignore` for generics or replace with precise types; keep `None` guard before `ping()`
- [ ] `app/services/auth/oauth.py`: explicit return types and safe JSON casts
- [ ] `app/services/middleware/rate_limiter.py`: type wrappers/generics; avoid `Any`
- [ ] `app/core/error_handling/error_handlers.py`: normalize `HTTPException.detail` typing
- [ ] `app/core/security/security.py`: return concrete `str`/`bool`
- [ ] `app/database/database.py`: keep `AsyncSession` generator annotated; remove unused ignores
- [ ] `app/api/users/{admin.py,auth.py,profile.py,search.py}` and `app/api/admin/users.py`: remove unused ignores; add return annotations
- [ ] (Optional) Migrate models to `Mapped[...]`/`mapped_column` incrementally across `app/models/**`

## Notes
- Keep edits incremental; make one category of fix at a time and re‑run the loop.
- Only add mypy overrides for modules that actually error in this template; avoid global weakening.
