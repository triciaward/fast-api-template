"""Administrative API endpoints."""

from fastapi import APIRouter

# Import admin routers
from .users import router as admin_users_router

# Create main admin router
router = APIRouter(prefix="/admin", tags=["administration"])

# Include admin sub-routers
router.include_router(admin_users_router)

__all__ = ["router"]
