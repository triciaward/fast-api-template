"""Authentication and session management services."""

from typing import TYPE_CHECKING

from .refresh_token import (
    create_user_session,
    get_device_info,
    refresh_access_token,
    revoke_all_sessions,
    revoke_session,
    utc_now,
)

if TYPE_CHECKING:  # for type checkers only
    from .oauth import OAuthService as _OAuthService

# Typed optional instance initialized via alias import
oauth_service: "_OAuthService | None"
try:
    from .oauth import OAuthService as _OAuthService

    oauth_service = _OAuthService()
except Exception:  # pragma: no cover - optional dependency path
    oauth_service = None

__all__ = [
    "oauth_service",
    "create_user_session",
    "get_device_info",
    "refresh_access_token",
    "revoke_all_sessions",
    "revoke_session",
    "utc_now",
]
