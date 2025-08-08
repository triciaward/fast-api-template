"""Core application functionality organized by category."""

# Import from organized subfolders for backward compatibility
# Keep imports lightweight to avoid circular dependencies during package init
from . import config, error_handling, security
from .config import (
    Settings,
    configure_cors,
    get_app_logger,
    get_auth_logger,
    settings,
    setup_logging,
)
from .error_handling import (
    AuthenticationException,
    AuthorizationException,
    BaseAPIException,
    ConflictException,
    NotFoundException,
    ValidationException,
    register_error_handlers,
)
from .security import (
    ValidationError,
    clean_input,
    configure_security_headers,
    create_access_token,
    generate_api_key,
    get_password_hash,
    hash_api_key,
    sanitize_input,
    validate_email_format,
    validate_password,
    validate_username,
    verify_api_key,
    verify_password,
)

__all__ = [
    # Configuration
    "Settings",
    "settings",
    "configure_cors",
    "get_app_logger",
    "get_auth_logger",
    "setup_logging",
    # Security
    "create_access_token",
    "generate_api_key",
    "get_password_hash",
    "hash_api_key",
    "verify_api_key",
    "verify_password",
    "configure_security_headers",
    "clean_input",
    "sanitize_input",
    "validate_email_format",
    "validate_password",
    "validate_username",
    "ValidationError",
    # Error handling
    "register_error_handlers",
    "BaseAPIException",
    "ConflictException",
    "NotFoundException",
    "AuthenticationException",
    "AuthorizationException",
    "ValidationException",
    # Category modules
    "config",
    "security",
    "error_handling",
]
