"""FastAPI application and API router setup."""

from fastapi import APIRouter

from app.core.config import settings

# Import domain routers
from . import admin, auth, system, users

# Create main API router
api_router = APIRouter()

# Include core domain routers
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(admin.router)
api_router.include_router(system.router)

# Conditionally include optional features
if settings.ENABLE_WEBSOCKETS:
    from . import integrations

    api_router.include_router(integrations.router)

__all__ = ["api_router"]
