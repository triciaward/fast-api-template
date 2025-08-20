# Services package for optional features organized by category
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar

from fastapi import Request

# Import from organized subfolders
if TYPE_CHECKING:
    from .auth import oauth_service as _oauth_service  # noqa: F401
try:
    from . import auth as _auth_mod

    oauth_service = _auth_mod.oauth_service
except Exception:  # pragma: no cover - optional path
    oauth_service = None

try:
    from . import external as _external_mod

    email_service = _external_mod.email_service
    redis_client = _external_mod.redis_client
except Exception:  # pragma: no cover - optional path
    email_service = None
    redis_client = None

# Background task services
# Predeclare optional callables so both branches are compatible
SubmitTask = Callable[..., Any | None]
GetTaskStatus = Callable[[str], dict[str, Any] | None]
CancelTask = Callable[[str], bool]
GetCeleryApp = Callable[[], Any]

submit_task: SubmitTask | None = None
get_task_status: GetTaskStatus | None = None
cancel_task: CancelTask | None = None
get_celery_app: GetCeleryApp | None = None


def _is_celery_enabled_fallback() -> bool:
    return False


def _get_active_tasks_fallback() -> list[dict[str, Any]]:
    return []


def _get_celery_stats_fallback() -> dict[str, Any]:
    return {"enabled": False}


is_celery_enabled: Callable[[], bool] = _is_celery_enabled_fallback
get_active_tasks: Callable[[], list[dict[str, Any]]] = _get_active_tasks_fallback
get_celery_stats: Callable[[], dict[str, Any]] = _get_celery_stats_fallback

try:
    from . import background as _bg_mod

    get_celery_app = _bg_mod.get_celery_app
    is_celery_enabled = _bg_mod.is_celery_enabled
    submit_task = _bg_mod.submit_task
    get_task_status = _bg_mod.get_task_status
    cancel_task = _bg_mod.cancel_task
    get_active_tasks = _bg_mod.get_active_tasks
    get_celery_stats = _bg_mod.get_celery_stats
except ImportError:  # pragma: no cover - optional path
    pass


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
    get_limiter = None
    # Create no-op decorators that just return the function unchanged

    _P = ParamSpec("_P")
    _R = TypeVar("_R")

    def _no_op_decorator(func: Callable[_P, _R]) -> Callable[_P, _R]:
        return func

    rate_limit_login = _no_op_decorator
    rate_limit_register = _no_op_decorator
    rate_limit_email_verification = _no_op_decorator
    rate_limit_password_reset = _no_op_decorator
    rate_limit_oauth = _no_op_decorator
    rate_limit_account_deletion = _no_op_decorator

    def rate_limit_custom(limit: str) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
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
