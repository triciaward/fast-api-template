# Adding Secure Features

A concise guide to add new endpoints and features safely.

## Quick rules
- Require JWT auth for user-facing routes: use `Depends(get_current_user)`.
- Use scoped API keys for system/automation routes: `Depends(require_api_scope("your:scope"))`.
- Put APIs under `/api` so strict cache headers apply.
- Add rate limits to login-like or abuse-prone actions.

## JWT-protected endpoint
```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.users.auth import get_current_user
from app.database.database import get_db
from app.schemas.auth.user import UserResponse

router = APIRouter()

@router.get("/example")
async def example_endpoint(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return {"ok": True}
```

## API key scope–protected endpoint
```python
from fastapi import APIRouter, Depends
from app.api.users.auth import require_api_scope
from app.schemas.auth.user import APIKeyUser

router = APIRouter()

@router.get("/system/example")
async def system_example(
    _: APIKeyUser = Depends(require_api_scope("system:read")),
) -> dict:
    return {"ok": True}
```

## Rate limiting high-risk routes
```python
from app.services import rate_limit_login

@router.post("/do-sensitive-thing")
@rate_limit_login
async def do_sensitive_thing():
    return {"ok": True}
```

## Security checklist
- Input validation with Pydantic schemas
- No secrets in responses/logs
- Use `Depends(get_db)` and commit/rollback properly in CRUD
- Keep `SECRET_KEY` safe; rotate credentials per environment
- Avoid returning raw ORM models; use schema objects

## Where to wire routes
- Create a router in your domain (e.g., `app/api/your_feature/your_routes.py`).
- Include it in `app/api/__init__.py` using `api_router.include_router(...)`.
- Keep naming consistent and endpoints under `settings.API_V1_STR`.

## Tests to add (minimal)
- Auth required (401 without token; 200 with valid token)
- Scope required (403 without scope; 200 with proper scope)
- Happy-path behavior and basic validation errors

See also: `docs/tutorials/authentication.md` for JWT/API keys, and `docs/tutorials/optional-features.md` for rate limiting and security headers.
