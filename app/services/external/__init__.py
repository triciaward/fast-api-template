"""External service integrations."""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

# Email service (optional)
if TYPE_CHECKING:
    from .email import EmailService as _EmailService
else:
    _EmailService = object  # runtime placeholder

email_service: "_EmailService | None"
try:
    from .email import EmailService as _EmailService

    email_service = _EmailService()
except ImportError:  # pragma: no cover - optional path
    email_service = None

redis_client: Any | None = None
init_redis: Callable[..., Any] | None = None
close_redis: Callable[..., Any] | None = None
get_redis_client: Callable[..., Any] | None = None
health_check_redis: Callable[..., Any] | None = None

try:  # pragma: no cover - optional path
    from . import redis as _redis

    redis_client = _redis.redis_client
    init_redis = _redis.init_redis
    close_redis = _redis.close_redis
    get_redis_client = _redis.get_redis_client
    health_check_redis = _redis.health_check_redis
except ImportError:
    pass

# Sentry (optional)
init_sentry: Callable[..., Any] | None = None
capture_exception: Callable[..., Any] | None = None
capture_message: Callable[..., Any] | None = None
set_request_context: Callable[..., Any] | None = None
set_user_context: Callable[..., Any] | None = None

try:  # pragma: no cover - optional path
    from . import sentry as _sentry

    init_sentry = _sentry.init_sentry
    capture_exception = _sentry.capture_exception
    capture_message = _sentry.capture_message
    set_request_context = _sentry.set_request_context
    set_user_context = _sentry.set_user_context
except ImportError:
    pass

__all__ = [
    "email_service",
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
