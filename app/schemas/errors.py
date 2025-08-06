"""
Standardized error response schemas.

This module provides consistent error response formats for all API endpoints.
All errors follow the same structure for better frontend integration.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorType(str, Enum):
    """Standard error types for consistent error categorization."""

    # Validation errors
    VALIDATION_ERROR = "ValidationError"
    INVALID_INPUT = "InvalidInput"

    # Authentication errors
    AUTHENTICATION_ERROR = "AuthenticationError"
    UNAUTHORIZED = "Unauthorized"
    INVALID_CREDENTIALS = "InvalidCredentials"
    TOKEN_EXPIRED = "TokenExpired"
    TOKEN_INVALID = "TokenInvalid"

    # Authorization errors
    AUTHORIZATION_ERROR = "AuthorizationError"
    FORBIDDEN = "Forbidden"
    INSUFFICIENT_PERMISSIONS = "InsufficientPermissions"

    # Resource errors
    NOT_FOUND = "NotFound"
    RESOURCE_NOT_FOUND = "ResourceNotFound"
    USER_NOT_FOUND = "UserNotFound"

    # Conflict errors
    CONFLICT = "Conflict"
    RESOURCE_EXISTS = "ResourceExists"
    DUPLICATE_EMAIL = "DuplicateEmail"
    DUPLICATE_USERNAME = "DuplicateUsername"

    # Rate limiting
    RATE_LIMIT_EXCEEDED = "RateLimitExceeded"

    # Server errors
    INTERNAL_SERVER_ERROR = "InternalServerError"
    SERVICE_UNAVAILABLE = "ServiceUnavailable"
    DATABASE_ERROR = "DatabaseError"

    # OAuth errors
    OAUTH_ERROR = "OAuthError"
    OAUTH_PROVIDER_ERROR = "OAuthProviderError"

    # Email errors
    EMAIL_ERROR = "EmailError"
    EMAIL_NOT_VERIFIED = "EmailNotVerified"

    # Password errors
    PASSWORD_ERROR = "PasswordError"
    PASSWORD_TOO_WEAK = "PasswordTooWeak"
    PASSWORD_MISMATCH = "PasswordMismatch"

    # Session errors
    SESSION_ERROR = "SessionError"
    SESSION_EXPIRED = "SessionExpired"
    TOO_MANY_SESSIONS = "TooManySessions"


class ErrorCode(str, Enum):
    """Standard error codes for programmatic error handling."""

    # Validation codes
    INVALID_EMAIL = "invalid_email"
    INVALID_USERNAME = "invalid_username"
    INVALID_PASSWORD = "invalid_password"
    INVALID_TOKEN = "invalid_token"
    INVALID_REQUEST = "invalid_request"

    # Authentication codes
    INVALID_CREDENTIALS = "invalid_credentials"
    TOKEN_EXPIRED = "token_expired"
    TOKEN_INVALID = "token_invalid"
    EMAIL_NOT_VERIFIED = "email_not_verified"

    # Authorization codes
    INSUFFICIENT_PERMISSIONS = "insufficient_permissions"
    SUPERUSER_REQUIRED = "superuser_required"

    # Resource codes
    USER_NOT_FOUND = "user_not_found"
    RESOURCE_NOT_FOUND = "resource_not_found"

    # Conflict codes
    CONFLICT = "conflict"
    EMAIL_ALREADY_EXISTS = "email_already_exists"
    USERNAME_ALREADY_EXISTS = "username_already_exists"

    # Rate limiting codes
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"

    # Server codes
    INTERNAL_ERROR = "internal_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    DATABASE_ERROR = "database_error"

    # OAuth codes
    OAUTH_PROVIDER_ERROR = "oauth_provider_error"
    OAUTH_NOT_CONFIGURED = "oauth_not_configured"

    # Email codes
    EMAIL_SEND_FAILED = "email_send_failed"

    # Password codes
    PASSWORD_TOO_WEAK = "password_too_weak"
    PASSWORD_MISMATCH = "password_mismatch"

    # Session codes
    SESSION_EXPIRED = "session_expired"
    TOO_MANY_SESSIONS = "too_many_sessions"


class ErrorResponse(BaseModel):
    """Standardized error response format."""

    error: "ErrorDetail" = Field(..., description="Error details")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": {
                    "type": "ValidationError",
                    "message": "Email is invalid",
                    "code": "invalid_email",
                }
            }
        }
    )


class ErrorDetail(BaseModel):
    """Detailed error information."""

    type: ErrorType = Field(..., description="Error type for categorization")
    message: str = Field(..., description="Human-readable error message")
    code: ErrorCode = Field(..., description="Machine-readable error code")
    details: dict[str, Any] | None = Field(
        None, description="Additional error details"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "ValidationError",
                "message": "Email is invalid",
                "code": "invalid_email",
                "details": {"field": "email", "value": "invalid-email"},
            }
        }
    )


class ValidationErrorDetail(ErrorDetail):
    """Validation error with field-specific details."""

    type: ErrorType = Field(default=ErrorType.VALIDATION_ERROR)
    field: str | None = Field(None, description="Field that failed validation")
    value: Any | None = Field(None, description="Invalid value provided")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "ValidationError",
                "message": "Email format is invalid",
                "code": "invalid_email",
                "field": "email",
                "value": "invalid-email",
            }
        }
    )


class AuthenticationErrorDetail(ErrorDetail):
    """Authentication error details."""

    type: ErrorType = Field(default=ErrorType.AUTHENTICATION_ERROR)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "AuthenticationError",
                "message": "Invalid email or password",
                "code": "invalid_credentials",
            }
        }
    )


class AuthorizationErrorDetail(ErrorDetail):
    """Authorization error details."""

    type: ErrorType = Field(default=ErrorType.AUTHORIZATION_ERROR)
    required_permissions: list[str] | None = Field(
        None, description="Required permissions for this operation"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "AuthorizationError",
                "message": "Superuser privileges required",
                "code": "superuser_required",
                "required_permissions": ["superuser"],
            }
        }
    )


class ResourceErrorDetail(ErrorDetail):
    """Resource not found error details."""

    type: ErrorType = Field(default=ErrorType.NOT_FOUND)
    resource_type: str | None = Field(None, description="Type of resource not found")
    resource_id: str | None = Field(None, description="ID of resource not found")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "NotFound",
                "message": "User not found",
                "code": "user_not_found",
                "resource_type": "user",
                "resource_id": "123e4567-e89b-12d3-a456-426614174000",
            }
        }
    )


class ConflictErrorDetail(ErrorDetail):
    """Conflict error details."""

    type: ErrorType = Field(default=ErrorType.CONFLICT)
    conflicting_field: str | None = Field(
        None, description="Field that caused the conflict"
    )
    conflicting_value: str | None = Field(
        None, description="Value that caused the conflict"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "Conflict",
                "message": "Email already registered",
                "code": "email_already_exists",
                "conflicting_field": "email",
                "conflicting_value": "user@example.com",
            }
        }
    )


class RateLimitErrorDetail(ErrorDetail):
    """Rate limit error details."""

    type: ErrorType = Field(default=ErrorType.RATE_LIMIT_EXCEEDED)
    retry_after: int | None = Field(
        None, description="Seconds to wait before retrying"
    )
    limit: int | None = Field(None, description="Rate limit threshold")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "RateLimitExceeded",
                "message": "Too many requests",
                "code": "rate_limit_exceeded",
                "retry_after": 60,
                "limit": 100,
            }
        }
    )


class ServerErrorDetail(ErrorDetail):
    """Server error details."""

    type: ErrorType = Field(default=ErrorType.INTERNAL_SERVER_ERROR)
    request_id: str | None = Field(None, description="Request ID for tracking")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "InternalServerError",
                "message": "An unexpected error occurred",
                "code": "internal_error",
                "request_id": "req_123456",
            }
        }
    )
