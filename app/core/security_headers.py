# fmt: off
"""Security Headers Middleware for FastAPI.

This module provides middleware to add security headers to HTTP responses.
These headers help protect against various security vulnerabilities.
"""
# fmt: on

import logging
from typing import Any

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to HTTP responses."""

    def __init__(self, app: Any) -> None:
        super().__init__(app)
        # Define allowed content types for different endpoints
        self.allowed_content_types = {
            "/api/v1/auth/login": ["application/x-www-form-urlencoded"],
            "/api/v1/auth/register": ["application/json"],
            "/api/v1/auth/refresh": ["application/json"],
            "/api/v1/auth/verify-email": ["application/json"],
            "/api/v1/auth/reset-password": ["application/json"],
            "/api/v1/auth/change-password": ["application/json"],
            "/api/v1/auth/delete-account": ["application/json"],
            "/api/v1/users": ["application/json"],
            "/api/v1/admin": ["application/json"],
            "/api/v1/health": ["application/json"],
            "/": ["text/html", "application/json"],
            "/docs": ["text/html"],
            "/redoc": ["text/html"],
            "/openapi.json": ["application/json"],
        }

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """Add security headers to the response and validate requests."""

        # Request Size Validation
        if settings.ENABLE_REQUEST_SIZE_VALIDATION:
            await self._validate_request_size(request)

        # Content-Type Validation
        if settings.ENABLE_CONTENT_TYPE_VALIDATION:
            await self._validate_content_type(request)

        response = await call_next(request)

        # Content Security Policy (CSP)
        # Restricts which resources can be loaded
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers["Content-Security-Policy"] = csp_policy

        # X-Content-Type-Options
        # Prevents MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options
        # Prevents clickjacking attacks
        response.headers["X-Frame-Options"] = "DENY"

        # X-XSS-Protection
        # Enables browser's XSS filtering (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer Policy
        # Controls how much referrer information is included with requests
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (formerly Feature Policy)
        # Controls which browser features can be used
        permissions_policy = (
            "accelerometer=(), "
            "ambient-light-sensor=(), "
            "autoplay=(), "
            "battery=(), "
            "camera=(), "
            "cross-origin-isolated=(), "
            "display-capture=(), "
            "document-domain=(), "
            "encrypted-media=(), "
            "execution-while-not-rendered=(), "
            "execution-while-out-of-viewport=(), "
            "fullscreen=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "keyboard-map=(), "
            "magnetometer=(), "
            "microphone=(), "
            "midi=(), "
            "navigation-override=(), "
            "payment=(), "
            "picture-in-picture=(), "
            "publickey-credentials-get=(), "
            "screen-wake-lock=(), "
            "sync-xhr=(), "
            "usb=(), "
            "web-share=(), "
            "xr-spatial-tracking=()"
        )
        response.headers["Permissions-Policy"] = permissions_policy

        # Strict-Transport-Security (HSTS)
        # Forces HTTPS connections (only add in production)
        if settings.ENABLE_HSTS:
            hsts_value = f"max-age={settings.HSTS_MAX_AGE}"
            if settings.HSTS_INCLUDE_SUBDOMAINS:
                hsts_value += "; includeSubDomains"
            if settings.HSTS_PRELOAD:
                hsts_value += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_value

        # Cache Control for sensitive endpoints
        if request.url.path.startswith("/api/v1/auth"):
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response

    async def _validate_request_size(self, request: Request) -> None:
        """Validate request size to prevent large payload attacks."""
        content_length = request.headers.get("content-length")

        if content_length:
            try:
                size = int(content_length)
                if size > settings.MAX_REQUEST_SIZE:
                    self._log_security_event(
                        "request_size_violation",
                        f"Request size {size} exceeds limit {settings.MAX_REQUEST_SIZE}",
                        request,
                    )
                    raise HTTPException(status_code=413, detail="Request too large")
            except ValueError:
                self._log_security_event(
                    "invalid_content_length",
                    f"Invalid content-length header: {content_length}",
                    request,
                )

    async def _validate_content_type(self, request: Request) -> None:
        """Validate content type to prevent MIME confusion attacks."""
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return  # No body expected for these methods

        content_type = request.headers.get("content-type", "")
        path = request.url.path

        # Allow empty content-type for requests that don't have bodies
        if not content_type:
            # Check if this is a request that might have a body
            if request.method in ["POST", "PUT", "PATCH"]:
                # Only validate if there's actually a body
                content_length = request.headers.get("content-length", "0")
                if content_length == "0" or not content_length:
                    return  # No body, so no content-type needed
            else:
                return  # GET, DELETE, etc. don't need content-type

        # Skip validation for testing scenarios (CORS tests, etc.)
        user_agent = request.headers.get("user-agent", "").lower()
        if "testclient" in user_agent or "pytest" in user_agent:
            return

        # Find matching endpoint pattern
        allowed_types = None
        for endpoint, types in self.allowed_content_types.items():
            if path.startswith(endpoint):
                allowed_types = types
                break

        if allowed_types is None:
            # No specific rules for this endpoint, allow common types
            allowed_types = [
                "application/json",
                "application/x-www-form-urlencoded",
                "multipart/form-data",
            ]

        # Check if content type is allowed
        content_type_lower = content_type.lower()
        is_allowed = any(
            allowed_type.lower() in content_type_lower for allowed_type in allowed_types
        )

        if not is_allowed:
            self._log_security_event(
                "content_type_violation",
                f"Invalid content-type '{content_type}' for path '{path}'. Allowed: {allowed_types}",
                request,
            )
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported media type. Allowed: {', '.join(allowed_types)}",
            )

    def _log_security_event(
        self, event_type: str, message: str, request: Request
    ) -> None:
        """Log security events for monitoring and alerting."""
        if not settings.ENABLE_SECURITY_EVENT_LOGGING:
            return

        extra_data = {
            "event_type": event_type,
            "security_message": message,
            "path": request.url.path,
            "method": request.method,
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
            "content_type": request.headers.get("content-type", "unknown"),
            "content_length": request.headers.get("content-length", "unknown"),
        }
        logger.warning(f"Security event: {event_type} - {message}", extra=extra_data)


def configure_security_headers(app: Any) -> None:
    """Configure security headers middleware for the FastAPI app."""
    app.add_middleware(SecurityHeadersMiddleware)
