"""External service integrations."""

# Try to import optional services
try:
    from .email import EmailService

    email_service = EmailService()
except ImportError:
    email_service = None  # type: ignore
    EmailService = None  # type: ignore

try:
    from .redis import (
        close_redis,
        get_redis_client,
        health_check_redis,
        init_redis,
        redis_client,
    )
except ImportError:
    redis_client = None
    init_redis = None  # type: ignore
    close_redis = None  # type: ignore
    get_redis_client = None  # type: ignore
    health_check_redis = None  # type: ignore

try:
    from .sentry import (
        capture_exception,
        capture_message,
        init_sentry,
        set_request_context,
        set_user_context,
    )
except ImportError:
    init_sentry = None  # type: ignore
    capture_exception = None  # type: ignore
    capture_message = None  # type: ignore

    set_request_context = None  # type: ignore
    set_user_context = None  # type: ignore

__all__ = [
    "email_service",
    "EmailService",
    "redis_client",
    "init_redis",
    "close_redis",
    "get_redis_client",
    "health_check_redis",
    "init_sentry",
    "capture_exception",
    "capture_message",
    "set_request_context",
    "set_user_context",
]
