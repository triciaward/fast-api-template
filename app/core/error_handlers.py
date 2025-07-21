"""
Centralized error handling for FastAPI application.

This module provides exception handlers that convert all errors to standardized
error responses for consistent API behavior.
"""

import uuid
from typing import Any, Optional, Union

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.logging_config import get_app_logger
from app.schemas.errors import (
    AuthenticationErrorDetail,
    AuthorizationErrorDetail,
    ConflictErrorDetail,
    ErrorCode,
    ErrorDetail,
    ErrorResponse,
    ErrorType,
    RateLimitErrorDetail,
    ResourceErrorDetail,
    ServerErrorDetail,
    ValidationErrorDetail,
)

logger = get_app_logger()


def create_error_response(
    error_detail: ErrorDetail, status_code: int = 500
) -> JSONResponse:
    """Create a standardized error response."""
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(error=error_detail).model_dump(),
    )


def get_request_id(request: Request) -> str:
    """Get or generate a request ID for tracking."""
    # Check if request ID already exists in headers
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())
    return request_id


async def validation_exception_handler(
    request: Request, exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    request_id = get_request_id(request)

    # Extract field errors from validation exception
    errors = []
    if hasattr(exc, "errors"):
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            value = error.get("input")
            message = error.get("msg", "Validation error")

            # Handle bytes values by converting to string
            if isinstance(value, bytes):
                try:
                    value = value.decode("utf-8")
                except UnicodeDecodeError:
                    value = str(value)

            errors.append(
                {
                    "field": field,
                    "value": value,
                    "message": message,
                    "type": error.get("type", "value_error"),
                }
            )

    # Create error detail
    error_detail = ValidationErrorDetail(
        message="Validation failed",
        code=ErrorCode.INVALID_REQUEST,
        details={"errors": errors},
        field=errors[0]["field"] if errors else None,
        value=errors[0]["value"] if errors else None,
    )

    logger.warning(
        "Validation error",
        request_id=request_id,
        path=request.url.path,
        errors=errors,
    )

    return create_error_response(error_detail, status_code=422)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions and convert to standardized format."""
    request_id = get_request_id(request)

    # Check if this is a custom StandardizedHTTPException
    if hasattr(exc, "error_type") and hasattr(exc, "error_code"):
        # This is a custom exception with standardized details
        error_type = exc.error_type
        error_code = exc.error_code
        details = getattr(exc, "error_details", {})

        # Create appropriate error detail based on type
        custom_error_detail: ErrorDetail
        if error_type == ErrorType.AUTHENTICATION_ERROR:
            custom_error_detail = AuthenticationErrorDetail(
                message=exc.detail,
                code=error_code,
                details=details,
            )
        elif error_type == ErrorType.AUTHORIZATION_ERROR:
            custom_error_detail = AuthorizationErrorDetail(
                message=exc.detail,
                code=error_code,
                required_permissions=details.get("required_permissions"),
                details=details,
            )
        elif error_type == ErrorType.NOT_FOUND:
            custom_error_detail = ResourceErrorDetail(
                message=exc.detail,
                code=error_code,
                resource_type=details.get("resource_type"),
                resource_id=details.get("resource_id"),
                details=details,
            )
        elif error_type == ErrorType.CONFLICT:
            custom_error_detail = ConflictErrorDetail(
                message=exc.detail,
                code=error_code,
                conflicting_field=details.get("conflicting_field"),
                conflicting_value=details.get("conflicting_value"),
                details=details,
            )
        elif error_type == ErrorType.VALIDATION_ERROR:
            custom_error_detail = ValidationErrorDetail(
                message=exc.detail,
                code=error_code,
                field=details.get("field"),
                value=details.get("value"),
                details=details,
            )
        elif error_type == ErrorType.RATE_LIMIT_EXCEEDED:
            custom_error_detail = RateLimitErrorDetail(
                message=exc.detail,
                code=error_code,
                retry_after=details.get("retry_after"),
                limit=details.get("limit"),
                details=details,
            )
        elif error_type == ErrorType.INTERNAL_SERVER_ERROR:
            custom_error_detail = ServerErrorDetail(
                message=exc.detail,
                code=error_code,
                request_id=details.get("request_id"),
                details=details,
            )
        else:
            custom_error_detail = ErrorDetail(
                type=error_type,
                message=exc.detail,
                code=error_code,
                details=details,
            )
    else:
        # This is a regular HTTPException - map to standardized format
        # Map status codes to error types
        status_to_error_type = {
            400: ErrorType.VALIDATION_ERROR,
            401: ErrorType.AUTHENTICATION_ERROR,
            403: ErrorType.AUTHORIZATION_ERROR,
            404: ErrorType.NOT_FOUND,
            409: ErrorType.CONFLICT,
            422: ErrorType.VALIDATION_ERROR,
            429: ErrorType.RATE_LIMIT_EXCEEDED,
            500: ErrorType.INTERNAL_SERVER_ERROR,
            503: ErrorType.SERVICE_UNAVAILABLE,
        }

        # Map common error messages to error codes
        detail_to_code = {
            "Could not validate credentials": ErrorCode.TOKEN_INVALID,
            "Not authenticated": ErrorCode.TOKEN_INVALID,
            "Invalid email or password": ErrorCode.INVALID_CREDENTIALS,
            "Invalid email or password. Please check your credentials and try again.": ErrorCode.INVALID_CREDENTIALS,
            "Email already registered": ErrorCode.EMAIL_ALREADY_EXISTS,
            "Email already registered. Please use a different email or try logging in.": ErrorCode.EMAIL_ALREADY_EXISTS,
            "Username already taken": ErrorCode.USERNAME_ALREADY_EXISTS,
            "User not found": ErrorCode.USER_NOT_FOUND,
            "Not Found": ErrorCode.RESOURCE_NOT_FOUND,
            "Superuser privileges required": ErrorCode.SUPERUSER_REQUIRED,
            "Please verify your email": ErrorCode.EMAIL_NOT_VERIFIED,
            "Invalid email format": ErrorCode.INVALID_EMAIL,
            "Invalid refresh token": ErrorCode.TOKEN_INVALID,
            "No refresh token provided": ErrorCode.TOKEN_INVALID,
        }

        error_type = status_to_error_type.get(
            exc.status_code, ErrorType.INTERNAL_SERVER_ERROR
        )

        # Handle case where exc.detail is a dict (not hashable)
        if isinstance(exc.detail, dict):
            error_code = ErrorCode.INVALID_REQUEST
            # Convert dict to string for message field
            message = str(exc.detail)
            # If dict has a 'message' key, use that as the primary message
            if "message" in exc.detail:
                message = str(exc.detail["message"])
        else:
            error_code = detail_to_code.get(exc.detail, ErrorCode.INVALID_REQUEST)
            message = exc.detail

        # Create appropriate error detail based on type
        error_detail: ErrorDetail
        if error_type == ErrorType.AUTHENTICATION_ERROR:
            error_detail = AuthenticationErrorDetail(
                message=message,
                code=error_code,
                details={},
            )
        elif error_type == ErrorType.AUTHORIZATION_ERROR:
            error_detail = AuthorizationErrorDetail(
                message=message,
                code=error_code,
                required_permissions=None,
                details={},
            )
        elif error_type == ErrorType.NOT_FOUND:
            error_detail = ResourceErrorDetail(
                message=message,
                code=error_code,
                resource_type=None,
                resource_id=None,
                details={},
            )
        elif error_type == ErrorType.CONFLICT:
            error_detail = ConflictErrorDetail(
                message=message,
                code=error_code,
                conflicting_field=None,
                conflicting_value=None,
                details={},
            )
        else:
            error_detail = ErrorDetail(
                type=error_type,
                message=message,
                code=error_code,
                details={},
            )

    logger.warning(
        "HTTP exception",
        request_id=request_id,
        path=request.url.path,
        status_code=exc.status_code,
        detail=exc.detail,
    )

    # Use the appropriate error detail variable
    final_error_detail = (
        custom_error_detail if "custom_error_detail" in locals() else error_detail
    )
    return create_error_response(final_error_detail, status_code=exc.status_code)


async def rate_limit_exception_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """Handle rate limit exceeded exceptions."""
    request_id = get_request_id(request)

    error_detail = RateLimitErrorDetail(
        message="Too many requests. Please try again later.",
        code=ErrorCode.RATE_LIMIT_EXCEEDED,
        retry_after=getattr(exc, "retry_after", 60),
        limit=getattr(exc, "limit", None),
        details={},
    )

    logger.warning(
        "Rate limit exceeded",
        request_id=request_id,
        path=request.url.path,
        retry_after=error_detail.retry_after,
    )

    return create_error_response(error_detail, status_code=429)


async def integrity_error_handler(
    request: Request, exc: IntegrityError
) -> JSONResponse:
    """Handle database integrity errors."""
    request_id = get_request_id(request)

    # Parse integrity error to determine the specific issue
    error_message = str(exc)
    error_code = ErrorCode.CONFLICT

    if "duplicate key" in error_message.lower():
        if "email" in error_message.lower():
            error_code = ErrorCode.EMAIL_ALREADY_EXISTS
            message = "Email already registered. Please use a different email or try logging in."
        elif "username" in error_message.lower():
            error_code = ErrorCode.USERNAME_ALREADY_EXISTS
            message = "Username already taken. Please choose a different username."
        else:
            message = "Resource already exists"
    else:
        message = "Database constraint violation"

    error_detail = ConflictErrorDetail(
        message=message,
        code=error_code,
        conflicting_field=None,
        conflicting_value=None,
        details={"database_error": error_message},
    )

    logger.error(
        "Database integrity error",
        request_id=request_id,
        path=request.url.path,
        error=error_message,
    )

    return create_error_response(error_detail, status_code=409)


async def sqlalchemy_error_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """Handle general SQLAlchemy errors."""
    request_id = get_request_id(request)

    error_detail = ServerErrorDetail(
        message="Database error occurred",
        code=ErrorCode.DATABASE_ERROR,
        request_id=request_id,
        details={"database_error": str(exc)},
    )

    logger.error(
        "Database error",
        request_id=request_id,
        path=request.url.path,
        error=str(exc),
        exc_info=True,
    )

    return create_error_response(error_detail, status_code=500)


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other unhandled exceptions."""
    request_id = get_request_id(request)

    error_detail = ServerErrorDetail(
        message="An unexpected error occurred",
        code=ErrorCode.INTERNAL_ERROR,
        request_id=request_id,
        details={"exception_type": type(exc).__name__},
    )

    logger.error(
        "Unhandled exception",
        request_id=request_id,
        path=request.url.path,
        error=str(exc),
        exc_info=True,
    )

    return create_error_response(error_detail, status_code=500)


def register_error_handlers(app) -> None:
    """Register all error handlers with the FastAPI application."""

    # Register exception handlers
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("Error handlers registered successfully")


def create_standardized_error(
    error_type: ErrorType,
    message: str,
    code: ErrorCode,
    status_code: int = 500,
    details: Optional[dict[str, Any]] = None,
) -> tuple[ErrorDetail, int]:
    """Helper function to create standardized errors."""

    error_detail = ErrorDetail(
        type=error_type,
        message=message,
        code=code,
        details=details,
    )

    return error_detail, status_code


def create_validation_error(
    message: str,
    code: ErrorCode,
    field: Optional[str] = None,
    value: Optional[Any] = None,
    details: Optional[dict[str, Any]] = None,
) -> tuple[ValidationErrorDetail, int]:
    """Helper function to create validation errors."""

    error_detail = ValidationErrorDetail(
        message=message,
        code=code,
        field=field,
        value=value,
        details=details,
    )

    return error_detail, 422


def create_authentication_error(
    message: str,
    code: ErrorCode = ErrorCode.INVALID_CREDENTIALS,
    details: Optional[dict[str, Any]] = None,
) -> tuple[AuthenticationErrorDetail, int]:
    """Helper function to create authentication errors."""

    error_detail = AuthenticationErrorDetail(
        message=message,
        code=code,
        details=details,
    )

    return error_detail, 401


def create_authorization_error(
    message: str,
    code: ErrorCode = ErrorCode.INSUFFICIENT_PERMISSIONS,
    required_permissions: Optional[list[str]] = None,
    details: Optional[dict[str, Any]] = None,
) -> tuple[AuthorizationErrorDetail, int]:
    """Helper function to create authorization errors."""

    error_detail = AuthorizationErrorDetail(
        message=message,
        code=code,
        required_permissions=required_permissions,
        details=details,
    )

    return error_detail, 403


def create_not_found_error(
    message: str,
    code: ErrorCode = ErrorCode.RESOURCE_NOT_FOUND,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> tuple[ResourceErrorDetail, int]:
    """Helper function to create not found errors."""

    error_detail = ResourceErrorDetail(
        message=message,
        code=code,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
    )

    return error_detail, 404


def create_conflict_error(
    message: str,
    code: ErrorCode = ErrorCode.CONFLICT,
    conflicting_field: Optional[str] = None,
    conflicting_value: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> tuple[ConflictErrorDetail, int]:
    """Helper function to create conflict errors."""

    error_detail = ConflictErrorDetail(
        message=message,
        code=code,
        conflicting_field=conflicting_field,
        conflicting_value=conflicting_value,
        details=details,
    )

    return error_detail, 409
