# Services package for optional features organized by category
from collections.abc import Callable
from typing import Any

from fastapi import Request

# Import from organized subfolders
try:
    from .auth import oauth_service
except ImportError:
    oauth_service = None  # type: ignore

try:
    from .external import email_service, redis_client
except ImportError:
    email_service = None  # type: ignore
    redis_client = None

# Background task services
try:
    from .background import (
        cancel_task,
        get_active_tasks,
        get_celery_app,
        get_celery_stats,
        get_task_status,
        is_celery_enabled,
        submit_task,
    )
except ImportError:
    # Fallback if Celery is not available
    get_celery_app = None  # type: ignore

    def is_celery_enabled() -> bool:
        return False

    submit_task = None  # type: ignore
    get_task_status = None  # type: ignore
    cancel_task = None  # type: ignore

    def get_active_tasks() -> list[dict[str, Any]]:
        return []

    def get_celery_stats() -> dict[str, Any]:
        return {"enabled": False}


# Rate limiting service
try:
    from .middleware import (
        get_limiter,
        get_rate_limit_info,
        rate_limit_account_deletion,
        rate_limit_custom,
        rate_limit_email_verification,
        rate_limit_login,
        rate_limit_oauth,
        rate_limit_password_reset,
        rate_limit_register,
        setup_rate_limiting,
    )
except ImportError:
    # Fallback if rate limiting is not available
    get_limiter = None  # type: ignore
    # Create no-op decorators that just return the function unchanged

    def _no_op_decorator(func: Any) -> Any:
        return func

    rate_limit_login = _no_op_decorator
    rate_limit_register = _no_op_decorator
    rate_limit_email_verification = _no_op_decorator
    rate_limit_password_reset = _no_op_decorator
    rate_limit_oauth = _no_op_decorator
    rate_limit_account_deletion = _no_op_decorator

    def rate_limit_custom(
        limit: str,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return _no_op_decorator

    def setup_rate_limiting(app: Any) -> None:
        return None

    def get_rate_limit_info(request: Request) -> dict[str, Any]:
        return {"enabled": False}


# Sentry monitoring (no-op if not available)
def init_sentry() -> None:
    """Initialize Sentry error monitoring (no-op if not available)."""


# Redis functions (no-op if not available)
async def init_redis() -> None:
    """Initialize Redis connection (no-op if not available)."""


async def close_redis() -> None:
    """Close Redis connection (no-op if not available)."""


# Rate limiter functions (no-op if not available)
async def init_rate_limiter() -> None:
    """Initialize rate limiting (no-op if not available)."""


__all__ = [
    "email_service",
    "oauth_service",
    "redis_client",
    "get_celery_app",
    "is_celery_enabled",
    "submit_task",
    "get_task_status",
    "cancel_task",
    "get_active_tasks",
    "get_celery_stats",
    "get_limiter",
    "rate_limit_login",
    "rate_limit_register",
    "rate_limit_email_verification",
    "rate_limit_password_reset",
    "rate_limit_oauth",
    "rate_limit_account_deletion",
    "rate_limit_custom",
    "setup_rate_limiting",
    "get_rate_limit_info",
    "init_sentry",
    "init_redis",
    "close_redis",
    "init_rate_limiter",
]
