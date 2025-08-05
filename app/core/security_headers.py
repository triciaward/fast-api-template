"""Security Headers Middleware for FastAPI.

This module provides middleware to add security headers to HTTP responses.
These headers help protect against various security vulnerabilities.
"""

from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to HTTP responses."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """Add security headers to the response."""
        response = await call_next(request)

        # Content Security Policy (CSP)
        # Restricts which resources can be loaded
        response.headers["Content-Security-Policy"] = (
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
        response.headers["Permissions-Policy"] = (
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


def configure_security_headers(app: Any) -> None:
    """Configure security headers middleware for the FastAPI app."""
    app.add_middleware(SecurityHeadersMiddleware)
