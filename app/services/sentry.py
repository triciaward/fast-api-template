"""Sentry/GlitchTip error monitoring service."""

import logging
from typing import Optional

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
        integrations = [FastApiIntegration()]

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
            # Add custom tags for better organization
            default_tags={
                "service": "fastapi-template",
                "version": settings.VERSION,
            },
            # Capture request body for better debugging (be careful with sensitive data)
            send_default_pii=False,
            # Enable debug mode in development
            debug=settings.ENVIRONMENT == "development",
        )

        logger.info(
            f"Sentry initialized for environment: {settings.SENTRY_ENVIRONMENT}"
        )

    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
        # Don't raise the exception - we don't want Sentry to break the app


def capture_exception(exception: Exception, context: Optional[dict] = None) -> None:
    """Capture an exception with optional context."""
    if not settings.ENABLE_SENTRY:
        return

    try:
        with sentry_sdk.push_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_tag(key, str(value))
            sentry_sdk.capture_exception(exception)
    except Exception as e:
        logger.error(f"Failed to capture exception in Sentry: {e}")


def capture_message(
    message: str, level: str = "info", context: Optional[dict] = None
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
    except Exception as e:
        logger.error(f"Failed to capture message in Sentry: {e}")


def set_user_context(
    user_id: Optional[int] = None, email: Optional[str] = None
) -> None:
    """Set user context for Sentry events."""
    if not settings.ENABLE_SENTRY:
        return

    try:
        if user_id or email:
            sentry_sdk.set_user(
                {
                    "id": str(user_id) if user_id else None,
                    "email": email,
                }
            )
    except Exception as e:
        logger.error(f"Failed to set user context in Sentry: {e}")


def clear_user_context() -> None:
    """Clear user context from Sentry events."""
    if not settings.ENABLE_SENTRY:
        return

    try:
        sentry_sdk.set_user(None)
    except Exception as e:
        logger.error(f"Failed to clear user context in Sentry: {e}")
