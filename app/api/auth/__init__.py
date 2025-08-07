"""Authentication API endpoints."""

from fastapi import APIRouter

# Import all auth routers
from .account_deletion import router as account_deletion_router
from .api_keys import router as api_keys_router
from .email_verification import router as email_verification_router
from .login import router as login_router
from .password_management import router as password_management_router
from .session_management import router as session_management_router

# Create main auth router
router = APIRouter(prefix="/auth", tags=["authentication"])

# Include all auth sub-routers
router.include_router(login_router)
router.include_router(password_management_router)
router.include_router(email_verification_router)
router.include_router(session_management_router)
router.include_router(account_deletion_router)
router.include_router(api_keys_router)

__all__ = ["router"]
