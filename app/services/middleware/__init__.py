"""Middleware services for request processing."""

from collections.abc import Callable
from typing import Any

from fastapi import Request

try:
    from .rate_limiter import (
        get_client_ip,
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
    # Fallback if rate limiting dependencies not available
    get_limiter = None  # type: ignore

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

    def get_client_ip(request: Request) -> str:
        return "unknown"


try:
    from .websocket import ConnectionManager

    websocket_manager = ConnectionManager()
except ImportError:
    ConnectionManager = None  # type: ignore
    websocket_manager = None  # type: ignore

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
