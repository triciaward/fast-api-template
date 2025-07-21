# Export all CRUD functions
# Import modules individually to avoid circular imports
from . import (
    api_key,
    audit_log,
    refresh_token,
    user,
)

# Export refresh_token CRUD functions for test and app imports
from .refresh_token import (
    cleanup_expired_tokens,
    create_refresh_token,
    enforce_session_limit,
    get_refresh_token_by_hash,
    get_user_session_count,
    get_user_sessions,
    revoke_all_user_sessions,
    revoke_refresh_token,
    revoke_refresh_token_by_hash,
    verify_refresh_token_in_db,
)
from .user import (
    authenticate_user_sync,
    create_oauth_user_sync,
    create_user_sync,
    get_user_by_email_sync,
    get_user_by_oauth_id_sync,
    get_user_by_username_sync,
    get_user_by_verification_token_sync,
    update_verification_token_sync,
    verify_user_sync,
)

__all__ = [
    "user",
    "refresh_token",
    "audit_log",
    "api_key",
    # refresh_token functions
    "cleanup_expired_tokens",
    "create_refresh_token",
    "enforce_session_limit",
    "get_refresh_token_by_hash",
    "get_user_session_count",
    "get_user_sessions",
    "revoke_all_user_sessions",
    "revoke_refresh_token",
    "revoke_refresh_token_by_hash",
    "verify_refresh_token_in_db",
    # user functions
    "authenticate_user_sync",
    "create_oauth_user_sync",
    "create_user_sync",
    "get_user_by_email_sync",
    "get_user_by_oauth_id_sync",
    "get_user_by_username_sync",
    "get_user_by_verification_token_sync",
    "update_verification_token_sync",
    "verify_user_sync",
]
