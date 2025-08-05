from fastapi import APIRouter

from app.api.api_v1.endpoints.auth import (
    account_deletion,
    api_keys,
    email_verification,
    login,
    password_management,
    session_management,
)

# Create the main auth router
router = APIRouter()

# Include all auth sub-routers
router.include_router(login.router, tags=["authentication"])
router.include_router(email_verification.router, tags=["authentication"])
router.include_router(password_management.router, tags=["authentication"])
router.include_router(account_deletion.router, tags=["authentication"])
router.include_router(session_management.router, tags=["authentication"])
router.include_router(api_keys.router, tags=["authentication"]) 