"""
Custom exception classes for the FastAPI template.

This module provides standardized exception classes for different types of errors,
making error handling more consistent and informative.
"""

from typing import Any

from fastapi import HTTPException, status

from app.schemas.core.errors import ErrorCode, ErrorType


class BaseAPIException(HTTPException):
    """Base exception class for API errors."""

    def __init__(
        self,
        status_code: int,
        message: str,
        error_type: ErrorType,
        error_code: ErrorCode,
        error_details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=message)
        self.message = message
        self.error_type = error_type
        self.error_code = error_code
        self.error_details = error_details or {}
        self.detail = message  # For backward compatibility


class ValidationError(BaseAPIException):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INVALID_REQUEST,
        field: str | None = None,
        value: Any = None,
        **kwargs: Any,
    ) -> None:
        error_details = {"field": field, "value": value, **kwargs}
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            error_type=ErrorType.VALIDATION_ERROR,
            error_code=code,
            error_details=error_details,
        )


class AuthenticationError(BaseAPIException):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        code: ErrorCode = ErrorCode.INVALID_CREDENTIALS,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            error_type=ErrorType.AUTHENTICATION_ERROR,
            error_code=code,
            error_details=kwargs,
        )


class AuthorizationError(BaseAPIException):
    """Raised when authorization fails."""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        code: ErrorCode = ErrorCode.INSUFFICIENT_PERMISSIONS,
        required_permissions: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        error_details = {"required_permissions": required_permissions, **kwargs}
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            error_type=ErrorType.AUTHORIZATION_ERROR,
            error_code=code,
            error_details=error_details,
        )


class ResourceNotFoundError(BaseAPIException):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.RESOURCE_NOT_FOUND,
        resource_type: str | None = None,
        resource_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        error_details = {
            "resource_type": resource_type,
            "resource_id": resource_id,
            **kwargs,
        }
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error_type=ErrorType.NOT_FOUND,
            error_code=code,
            error_details=error_details,
        )


class ConflictError(BaseAPIException):
    """Raised when there's a conflict with existing data."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.CONFLICT,
        conflicting_field: str | None = None,
        conflicting_value: str | None = None,
        **kwargs: Any,
    ) -> None:
        error_details = {
            "conflicting_field": conflicting_field,
            "conflicting_value": conflicting_value,
            **kwargs,
        }
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            error_type=ErrorType.CONFLICT,
            error_code=code,
            error_details=error_details,
        )


class RateLimitError(BaseAPIException):
    """Raised when rate limiting is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
        **kwargs: Any,
    ) -> None:
        error_details = {"retry_after": retry_after, **kwargs}
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            message=message,
            error_type=ErrorType.RATE_LIMIT_EXCEEDED,
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            error_details=error_details,
        )


class DatabaseError(BaseAPIException):
    """Raised when database operations fail."""

    def __init__(
        self,
        message: str = "Database operation failed",
        operation: str | None = None,
        **kwargs: Any,
    ) -> None:
        error_details = {"operation": operation, **kwargs}
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            error_type=ErrorType.DATABASE_ERROR,
            error_code=ErrorCode.DATABASE_ERROR,
            error_details=error_details,
        )


class ExternalServiceError(BaseAPIException):
    """Raised when external service calls fail."""

    def __init__(
        self,
        message: str = "External service error",
        service_name: str | None = None,
        **kwargs: Any,
    ) -> None:
        error_details = {"service_name": service_name, **kwargs}
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            message=message,
            error_type=ErrorType.SERVICE_UNAVAILABLE,
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
            error_details=error_details,
        )


class ConfigurationError(BaseAPIException):
    """Raised when there's a configuration issue."""

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        error_details = {"config_key": config_key, **kwargs}
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.INTERNAL_ERROR,
            error_details=error_details,
        )


class BusinessLogicError(BaseAPIException):
    """Raised when business logic validation fails."""

    def __init__(
        self,
        message: str,
        business_rule: str | None = None,
        **kwargs: Any,
    ) -> None:
        error_details = {"business_rule": business_rule, **kwargs}
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
            error_type=ErrorType.VALIDATION_ERROR,
            error_code=ErrorCode.INVALID_REQUEST,
            error_details=error_details,
        )


# Convenience functions for common error scenarios
def raise_validation_error(
    message: str,
    code: ErrorCode = ErrorCode.INVALID_REQUEST,
    field: str | None = None,
    value: Any = None,
) -> None:
    """Raise a validation error."""
    raise ValidationException(message=message, code=code, field=field, value=value)


def raise_not_found_error(
    message: str,
    code: ErrorCode = ErrorCode.RESOURCE_NOT_FOUND,
    resource_type: str | None = None,
    resource_id: str | None = None,
) -> None:
    """Raise a resource not found error."""
    raise NotFoundException(
        message=message,
        code=code,
        resource_type=resource_type,
        resource_id=resource_id,
    )


def raise_conflict_error(
    message: str,
    code: ErrorCode = ErrorCode.CONFLICT,
    conflicting_field: str | None = None,
    conflicting_value: str | None = None,
) -> None:
    """Raise a conflict error."""
    raise ConflictException(
        message=message,
        code=code,
        conflicting_field=conflicting_field,
        conflicting_value=conflicting_value,
    )


def raise_rate_limit_error(
    message: str = "Rate limit exceeded",
    retry_after: int | None = None,
) -> None:
    """Raise a rate limit error."""
    raise RateLimitError(message=message, retry_after=retry_after)


# Alias classes for backward compatibility with tests
class AuthenticationException(AuthenticationError):
    """Alias for AuthenticationError for backward compatibility."""


class AuthorizationException(AuthorizationError):
    """Alias for AuthorizationError for backward compatibility."""


class NotFoundException(ResourceNotFoundError):
    """Alias for ResourceNotFoundError for backward compatibility."""


class ConflictException(ConflictError):
    """Alias for ConflictError for backward compatibility."""


class ValidationException(ValidationError):
    """Alias for ValidationError for backward compatibility."""


# Additional helper functions for backward compatibility
def raise_authentication_error(
    message: str = "Authentication failed",
    code: ErrorCode = ErrorCode.INVALID_CREDENTIALS,
    **kwargs: Any,
) -> None:
    """Raise an authentication error."""
    raise AuthenticationException(message=message, code=code, **kwargs)


def raise_authorization_error(
    message: str = "Insufficient permissions",
    code: ErrorCode = ErrorCode.INSUFFICIENT_PERMISSIONS,
    **kwargs: Any,
) -> None:
    """Raise an authorization error."""
    raise AuthorizationException(message=message, code=code, **kwargs)
