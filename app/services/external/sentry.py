"""Sentry/GlitchTip error monitoring service."""

import logging
from typing import Any

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.core.config import settings

logger = logging.getLogger(__name__)


def init_sentry() -> None:
    """Initialize Sentry SDK for error monitoring."""
    if not settings.ENABLE_SENTRY or not settings.SENTRY_DSN:
        logger.info("Sentry monitoring disabled - no DSN provided")
        return

    try:
        # Configure integrations based on enabled features
        integrations: list[
            FastApiIntegration
            | SqlalchemyIntegration
            | RedisIntegration
            | CeleryIntegration
        ] = [FastApiIntegration()]

        # Add SQLAlchemy integration for database monitoring
        integrations.append(SqlalchemyIntegration())

        # Add Redis integration if enabled
        if settings.ENABLE_REDIS:
            integrations.append(RedisIntegration())

        # Add Celery integration if enabled
        if settings.ENABLE_CELERY:
            integrations.append(CeleryIntegration())

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
            integrations=integrations,
            # Capture request body for better debugging (be careful with sensitive data)
            send_default_pii=False,
            # Enable debug mode in development
            debug=settings.ENVIRONMENT == "development",
        )

        # Set custom tags after initialization
        sentry_sdk.set_tag("service", "fastapi-template")
        sentry_sdk.set_tag("version", settings.VERSION)

        logger.info(
            f"Sentry initialized for environment: {settings.SENTRY_ENVIRONMENT}",
        )

    except Exception:
        logger.exception("Failed to initialize Sentry")
        # Don't raise the exception - we don't want Sentry to break the app


def is_sentry_working() -> bool:
    """Check if Sentry is properly configured and working."""
    if not settings.ENABLE_SENTRY:
        return False

    try:
        from sentry_sdk.transport import HttpTransport

        client = sentry_sdk.Hub.current.client
        return client is not None and isinstance(client.transport, HttpTransport)
    except Exception:
        return False


def capture_exception(exception: Exception, context: dict[str, Any] | None = None) -> None:
    """Capture an exception with optional context."""
    if not settings.ENABLE_SENTRY:
        return

    try:
        with sentry_sdk.push_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_tag(key, str(value))
            sentry_sdk.capture_exception(exception)
    except Exception:
        # Fail-silent fallback - never let error logging cause new failures
        pass


def capture_message(
    message: str,
    level: str = "info",
    context: dict[str, Any] | None = None,
) -> None:
    """Capture a message with optional context."""
    if not settings.ENABLE_SENTRY:
        return

    try:
        with sentry_sdk.push_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_tag(key, str(value))
            sentry_sdk.capture_message(message, level=level)
    except Exception:
        # Fail-silent fallback - never let error logging cause new failures
        pass


def set_user_context(user_id: int | None = None, email: str | None = None) -> None:
    """Set user context for Sentry events."""
    if not settings.ENABLE_SENTRY:
        return

    try:
        if user_id or email:
            sentry_sdk.set_user(
                {
                    "id": str(user_id) if user_id else None,
                    "email": email,
                },
            )
    except Exception:
        # Fail-silent fallback - never let error logging cause new failures
        pass


def clear_user_context() -> None:
    """Clear user context from Sentry events."""
    if not settings.ENABLE_SENTRY:
        return

    try:
        sentry_sdk.set_user(None)
    except Exception:
        # Fail-silent fallback - never let error logging cause new failures
        pass


def set_request_context(request: Any) -> None:
    """Set request context for Sentry events (for use in middleware)."""
    if not settings.ENABLE_SENTRY:
        return

    try:
        # Set request context for better error tracking
        with sentry_sdk.configure_scope() as scope:
            scope.set_context(
                "request",
                {
                    "method": request.method,
                    "url": str(request.url),
                    "headers": dict(request.headers),
                    "query_params": dict(request.query_params),
                },
            )
    except Exception:
        # Fail-silent fallback - never let error logging cause new failures
        pass
