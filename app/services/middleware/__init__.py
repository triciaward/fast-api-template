"""Middleware services for request processing."""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar

from fastapi import Request

P = ParamSpec("P")
R = TypeVar("R")

# Declare placeholders once
get_limiter: Callable[..., Any] | None = None


def _no_op_decorator(func: Callable[P, R]) -> Callable[P, R]:
    return func


rate_limit_login: Callable[[Callable[P, R]], Callable[P, R]] = _no_op_decorator
rate_limit_register: Callable[[Callable[P, R]], Callable[P, R]] = _no_op_decorator
rate_limit_email_verification: Callable[[Callable[P, R]], Callable[P, R]] = (
    _no_op_decorator
)
rate_limit_password_reset: Callable[[Callable[P, R]], Callable[P, R]] = _no_op_decorator
rate_limit_oauth: Callable[[Callable[P, R]], Callable[P, R]] = _no_op_decorator
rate_limit_account_deletion: Callable[[Callable[P, R]], Callable[P, R]] = (
    _no_op_decorator
)


def rate_limit_custom(limit: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    return _no_op_decorator


def setup_rate_limiting(app: Any) -> None:
    return None


if TYPE_CHECKING:
    from .rate_limiter import RateLimitInfoTD as _RateLimitInfoTD
else:
    _RateLimitInfoTD = dict[str, Any]  # type: ignore[valid-type]


def get_rate_limit_info(request: Request) -> "_RateLimitInfoTD":
    return {"enabled": False}


def get_client_ip(request: Request) -> str:
    return "unknown"


# Bind real implementations if available
try:  # pragma: no cover - optional path
    from . import rate_limiter as _rl

    get_limiter = _rl.get_limiter
    rate_limit_login = _rl.rate_limit_login
    rate_limit_register = _rl.rate_limit_register
    rate_limit_email_verification = _rl.rate_limit_email_verification
    rate_limit_password_reset = _rl.rate_limit_password_reset
    rate_limit_oauth = _rl.rate_limit_oauth
    rate_limit_account_deletion = _rl.rate_limit_account_deletion
    rate_limit_custom = _rl.rate_limit_custom
    setup_rate_limiting = _rl.setup_rate_limiting
    get_rate_limit_info = _rl.get_rate_limit_info
    get_client_ip = _rl.get_client_ip
except Exception:
    pass


try:  # pragma: no cover - optional path
    from .websockets import ConnectionManager as ConnectionManager

    websocket_manager: "ConnectionManager | None" = ConnectionManager()
except Exception:
    # Fallback: no ConnectionManager symbol; tests expect getattr(..., "ConnectionManager", None) is None
    websocket_manager = None

__all__ = [
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
    "get_client_ip",
    "ConnectionManager",
    "websocket_manager",
]
