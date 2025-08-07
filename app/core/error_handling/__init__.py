"""Error handling and custom exceptions."""

from .error_handlers import register_error_handlers
from .exceptions import (
    AuthenticationException,
    AuthorizationException,
    BaseAPIException,
    ConflictException,
    NotFoundException,
    ValidationException,
)

__all__ = [
    # Error handlers
    "register_error_handlers",

    # Custom exceptions
    "BaseAPIException",
    "ConflictException",
    "NotFoundException",
    "AuthenticationException",
    "AuthorizationException",
    "ValidationException",
]
