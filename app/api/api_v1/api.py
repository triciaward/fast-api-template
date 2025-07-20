from fastapi import APIRouter

from app.api.api_v1.endpoints import admin, auth, health, users
from app.core.config import settings


def create_api_router() -> APIRouter:
    """Create the API router dynamically based on current settings."""
    api_router = APIRouter()
    api_router.include_router(
        auth.router, prefix="/auth", tags=["authentication"])
    api_router.include_router(users.router, prefix="/users", tags=["users"])
    api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
    api_router.include_router(health.router, tags=["health"])

    # Conditionally include WebSocket routes if enabled
    if settings.ENABLE_WEBSOCKETS:
        from app.api.api_v1.endpoints import ws_demo

        api_router.include_router(ws_demo.router, tags=["websockets"])

    # Conditionally include Celery routes if enabled
    if settings.ENABLE_CELERY:
        from app.api.api_v1.endpoints import celery

        api_router.include_router(
            celery.router, prefix="/celery", tags=["celery"])

    return api_router


# Create the router instance
api_router = create_api_router()
