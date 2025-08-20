# Release 1.2.2 — 2025-08-20

## Highlights
- Professional strict typing baseline with SQLAlchemy 2.0 typed ORM (`Mapped[...]`, `mapped_column(...)`, typed `relationship(...)`).
- Cleaner service initializers and robust optional feature fallbacks (Celery, middleware).
- CI polish: separate jobs with clear names, pip cache, and green pre-commit.

## What Changed
- Typing:
  - Migrated models and mixins to SQLAlchemy 2.0 typed style.
  - Introduced `TYPE_CHECKING` guards and typed placeholders for optional imports.
  - Decorator typing via `ParamSpec`/`TypeVar`; async support with `Awaitable`.
  - Normalized dynamic values and removed stale `type: ignore` comments.
- Services:
  - Celery fallbacks return `None` for optional callables when symbols are absent; stats/status helpers return safe defaults.
  - Import in `app/main.py` uses `importlib.import_module("app.services.background.celery_tasks")` so tests can capture imports.
- API:
  - Root endpoint returns a simple dict to avoid import-time Pydantic surface.
- CI & Tooling:
  - Jobs split into Lint, Type Check (mypy), and Tests with explicit names.
  - Pre-commit runs ruff/black/mypy; validate script kept in sync.

## Results
- Tests: 570 passed, 10 skipped.
- mypy (app): 0 errors.
- Ruff/Black: clean.

## Upgrade Notes
- No breaking changes to public APIs.
- If you used internals from `app.services` directly, note the optional fallbacks can be `None` unless the feature is enabled.

---

Happy coding! 🚀
