"""External integrations and real-time API endpoints."""

from fastapi import APIRouter

# Import integration routers
from .websockets import router as websockets_router

# Create main integrations router
router = APIRouter(prefix="/integrations", tags=["integrations"])

# Include integration sub-routers
router.include_router(websockets_router)

__all__ = ["router"]
