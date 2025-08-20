"""
Core user profile endpoints.

This module provides the essential profile endpoints for user self-service,
including viewing current user information and API key authentication.
"""

from fastapi import APIRouter, Depends

from app.api.users.auth import get_api_key_user, get_current_user
from app.schemas.auth.user import APIKeyUser, UserResponse

router = APIRouter()


@router.get("/me")
async def read_current_user(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """Get current user information via JWT token authentication."""
    return current_user


@router.get("/me/api-key")
async def read_current_user_api_key(
    api_key_user: APIKeyUser = Depends(get_api_key_user),
) -> APIKeyUser:
    """Get current user information via API key authentication."""
    return api_key_user
