"""Authentication and session management services."""

from .oauth import OAuthService
from .refresh_token import (
    create_user_session,
    get_device_info,
    refresh_access_token,
    revoke_all_sessions,
    revoke_session,
    utc_now,
)

# Try to create service instances
try:
    oauth_service = OAuthService()
except ImportError:
    oauth_service = None  # type: ignore

__all__ = [
    "oauth_service",
    "OAuthService",
    "create_user_session",
    "get_device_info",
    "refresh_access_token",
    "revoke_all_sessions",
    "revoke_session",
    "utc_now",
]
