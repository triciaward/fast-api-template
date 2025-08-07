"""User management API endpoints."""

from fastapi import APIRouter

# Import user routers
from .admin import router as admin_router
from .profile import router as profile_router
from .search import router as search_router

# Create main users router
router = APIRouter(prefix="/users", tags=["users"])

# Include user sub-routers
router.include_router(profile_router)
router.include_router(search_router)
router.include_router(admin_router)

__all__ = ["router"]
