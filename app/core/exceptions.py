"""
Custom exceptions for the FastAPI application.

This module provides custom exception classes that integrate with the
standardized error handling system.
"""

from typing import Any, Optional

from fastapi import HTTPException

from app.schemas.errors import (
    ErrorCode,
    ErrorType,
)


class StandardizedHTTPException(HTTPException):
    """Custom HTTP exception with standardized error details."""

    def __init__(
        self,
        status_code: int,
        error_type: ErrorType,
        message: str,
        code: ErrorCode,
        details: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        self.error_type = error_type
        self.error_code = code
        self.error_details = details or {}

        super().__init__(status_code=status_code, detail=message, headers=headers)


class ValidationException(StandardizedHTTPException):
    """Exception for validation errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INVALID_REQUEST,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        if field:
            details = details or {}
            details["field"] = field
        if value:
            details = details or {}
            details["value"] = value

        super().__init__(
            status_code=422,
            error_type=ErrorType.VALIDATION_ERROR,
            message=message,
            code=code,
            details=details,
        )


class AuthenticationException(StandardizedHTTPException):
    """Exception for authentication errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INVALID_CREDENTIALS,
        details: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        super().__init__(
            status_code=401,
            error_type=ErrorType.AUTHENTICATION_ERROR,
            message=message,
            code=code,
            details=details,
            headers=headers,
        )


class AuthorizationException(StandardizedHTTPException):
    """Exception for authorization errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INSUFFICIENT_PERMISSIONS,
        required_permissions: Optional[list[str]] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        if required_permissions:
            details = details or {}
            details["required_permissions"] = required_permissions

        super().__init__(
            status_code=403,
            error_type=ErrorType.AUTHORIZATION_ERROR,
            message=message,
            code=code,
            details=details,
        )


class NotFoundException(StandardizedHTTPException):
    """Exception for resource not found errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.RESOURCE_NOT_FOUND,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        if resource_type:
            details = details or {}
            details["resource_type"] = resource_type
        if resource_id:
            details = details or {}
            details["resource_id"] = resource_id

        super().__init__(
            status_code=404,
            error_type=ErrorType.NOT_FOUND,
            message=message,
            code=code,
            details=details,
        )


class ConflictException(StandardizedHTTPException):
    """Exception for conflict errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.CONFLICT,
        conflicting_field: Optional[str] = None,
        conflicting_value: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        if conflicting_field:
            details = details or {}
            details["conflicting_field"] = conflicting_field
        if conflicting_value:
            details = details or {}
            details["conflicting_value"] = conflicting_value

        super().__init__(
            status_code=409,
            error_type=ErrorType.CONFLICT,
            message=message,
            code=code,
            details=details,
        )


class RateLimitException(StandardizedHTTPException):
    """Exception for rate limit errors."""

    def __init__(
        self,
        message: str = "Too many requests. Please try again later.",
        retry_after: Optional[int] = None,
        limit: Optional[int] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        if retry_after:
            details = details or {}
            details["retry_after"] = retry_after
        if limit:
            details = details or {}
            details["limit"] = limit

        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)

        super().__init__(
            status_code=429,
            error_type=ErrorType.RATE_LIMIT_EXCEEDED,
            message=message,
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            details=details,
            headers=headers,
        )


class ServerException(StandardizedHTTPException):
    """Exception for server errors."""

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        request_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        if request_id:
            details = details or {}
            details["request_id"] = request_id

        super().__init__(
            status_code=500,
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            message=message,
            code=code,
            details=details,
        )


class ServiceUnavailableException(StandardizedHTTPException):
    """Exception for service unavailable errors."""

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        code: ErrorCode = ErrorCode.SERVICE_UNAVAILABLE,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            status_code=503,
            error_type=ErrorType.SERVICE_UNAVAILABLE,
            message=message,
            code=code,
            details=details,
        )


# Convenience functions for common error scenarios
def raise_validation_error(
    message: str,
    code: ErrorCode = ErrorCode.INVALID_REQUEST,
    field: Optional[str] = None,
    value: Optional[Any] = None,
    details: Optional[dict[str, Any]] = None,
) -> None:
    """Raise a validation error."""
    raise ValidationException(
        message=message,
        code=code,
        field=field,
        value=value,
        details=details,
    )


def raise_authentication_error(
    message: str,
    code: ErrorCode = ErrorCode.INVALID_CREDENTIALS,
    details: Optional[dict[str, Any]] = None,
    headers: Optional[dict[str, str]] = None,
) -> None:
    """Raise an authentication error."""
    raise AuthenticationException(
        message=message,
        code=code,
        details=details,
        headers=headers,
    )


def raise_authorization_error(
    message: str,
    code: ErrorCode = ErrorCode.INSUFFICIENT_PERMISSIONS,
    required_permissions: Optional[list[str]] = None,
    details: Optional[dict[str, Any]] = None,
) -> None:
    """Raise an authorization error."""
    raise AuthorizationException(
        message=message,
        code=code,
        required_permissions=required_permissions,
        details=details,
    )


def raise_not_found_error(
    message: str,
    code: ErrorCode = ErrorCode.RESOURCE_NOT_FOUND,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> None:
    """Raise a not found error."""
    raise NotFoundException(
        message=message,
        code=code,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
    )


def raise_conflict_error(
    message: str,
    code: ErrorCode = ErrorCode.CONFLICT,
    conflicting_field: Optional[str] = None,
    conflicting_value: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> None:
    """Raise a conflict error."""
    raise ConflictException(
        message=message,
        code=code,
        conflicting_field=conflicting_field,
        conflicting_value=conflicting_value,
        details=details,
    )


def raise_rate_limit_error(
    message: str = "Too many requests. Please try again later.",
    retry_after: Optional[int] = None,
    limit: Optional[int] = None,
    details: Optional[dict[str, Any]] = None,
) -> None:
    """Raise a rate limit error."""
    raise RateLimitException(
        message=message,
        retry_after=retry_after,
        limit=limit,
        details=details,
    )


def raise_server_error(
    message: str = "An unexpected error occurred",
    code: ErrorCode = ErrorCode.INTERNAL_ERROR,
    request_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> None:
    """Raise a server error."""
    raise ServerException(
        message=message,
        code=code,
        request_id=request_id,
        details=details,
    )


def raise_service_unavailable_error(
    message: str = "Service temporarily unavailable",
    code: ErrorCode = ErrorCode.SERVICE_UNAVAILABLE,
    details: Optional[dict[str, Any]] = None,
) -> None:
    """Raise a service unavailable error."""
    raise ServiceUnavailableException(
        message=message,
        code=code,
        details=details,
    )
