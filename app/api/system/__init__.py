"""System and monitoring API endpoints."""

from fastapi import APIRouter

from app.core.config import settings

# Import system routers
from .health import router as health_router

# Create main system router
router = APIRouter(prefix="/system", tags=["system"])

# Include system sub-routers
router.include_router(health_router)

# Conditionally include Celery routes if enabled
if settings.ENABLE_CELERY:
    from .background_tasks import router as background_tasks_router

    router.include_router(background_tasks_router)

__all__ = ["router"]
