# Services package for optional features like Redis and WebSockets
from typing import Any, Callable

from fastapi import Request

# Try to import optional services
try:
    from .email import email_service
except ImportError:
    email_service = None  # type: ignore

try:
    from .oauth import oauth_service
except ImportError:
    oauth_service = None  # type: ignore

try:
    from .redis import redis_client
except ImportError:
    redis_client = None

# Celery service
try:
    from .celery import (
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
    from .rate_limiter import (
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

    def rate_limit_custom(limit: str) -> Callable[[Callable], Callable]:
        return _no_op_decorator

    def setup_rate_limiting(app: Any) -> None:
        return None

    def get_rate_limit_info(request: Request) -> dict[str, Any]:
        return {"enabled": False}

# Note: websocket_manager doesn't exist in websocket.py, so we'll skip it for now

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
]
