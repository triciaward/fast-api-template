"""Rate limiting service using slowapi with support for both memory and Redis backends."""

from collections.abc import Callable
from typing import Any, ParamSpec, TypedDict, TypeVar

from fastapi import Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings

# Global limiter instance
limiter: Limiter | None = None


def get_limiter() -> Limiter:
    """Get or create the rate limiter instance."""
    global limiter

    if limiter is None:
        # Choose storage backend based on configuration
        if settings.ENABLE_REDIS and settings.RATE_LIMIT_STORAGE_BACKEND == "redis":
            # Use Redis backend if available and configured
            from app.services.external.redis import get_redis_client

            redis_client = get_redis_client()
            if redis_client:
                limiter = Limiter(
                    key_func=get_remote_address,
                    storage_uri=settings.REDIS_URL,
                    default_limits=[settings.RATE_LIMIT_DEFAULT],
                )
            else:
                # Fallback to memory if Redis is not available
                limiter = Limiter(
                    key_func=get_remote_address,
                    default_limits=[settings.RATE_LIMIT_DEFAULT],
                )
        else:
            # Use in-memory storage (default)
            limiter = Limiter(
                key_func=get_remote_address,
                default_limits=[settings.RATE_LIMIT_DEFAULT],
            )

    return limiter


def get_client_ip(request: Request) -> str:
    """Get client IP address, handling proxy headers."""
    # Check for forwarded headers first (for proxy setups)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(",")[0].strip()

    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fallback to remote address
    return str(get_remote_address(request))


# No-op decorator for when rate limiting is disabled
P = ParamSpec("P")
R = TypeVar("R")


def _no_op_decorator(func: Callable[P, R]) -> Callable[P, R]:
    """No-op decorator that returns the function unchanged."""
    return func


# Rate limiting decorators
def rate_limit_login(func: Callable[P, R]) -> Callable[P, R]:
    """Rate limit decorator for login endpoints."""
    if not settings.ENABLE_RATE_LIMITING:
        return _no_op_decorator(func)

    # Use slowapi's limit decorator
    return get_limiter().limit(settings.RATE_LIMIT_LOGIN)(func)  # type: ignore[misc]


def rate_limit_register(func: Callable[P, R]) -> Callable[P, R]:
    """Rate limit decorator for registration endpoints."""
    if not settings.ENABLE_RATE_LIMITING:
        return _no_op_decorator(func)

    # Use slowapi's limit decorator
    return get_limiter().limit(settings.RATE_LIMIT_REGISTER)(func)  # type: ignore[misc]


def rate_limit_email_verification(func: Callable[P, R]) -> Callable[P, R]:
    """Rate limit decorator for email verification endpoints."""
    if not settings.ENABLE_RATE_LIMITING:
        return _no_op_decorator(func)

    # Use slowapi's limit decorator
    return get_limiter().limit(settings.RATE_LIMIT_EMAIL_VERIFICATION)(func)  # type: ignore[misc]


def rate_limit_password_reset(func: Callable[P, R]) -> Callable[P, R]:
    """Rate limit decorator for password reset endpoints."""
    if not settings.ENABLE_RATE_LIMITING:
        return _no_op_decorator(func)

    # Use slowapi's limit decorator
    return get_limiter().limit(settings.RATE_LIMIT_PASSWORD_RESET)(func)  # type: ignore[misc]


def rate_limit_oauth(func: Callable[P, R]) -> Callable[P, R]:
    """Rate limit decorator for OAuth endpoints."""
    if not settings.ENABLE_RATE_LIMITING:
        return _no_op_decorator(func)

    # Use slowapi's limit decorator
    return get_limiter().limit(settings.RATE_LIMIT_OAUTH)(func)  # type: ignore[misc]


def rate_limit_account_deletion(func: Callable[P, R]) -> Callable[P, R]:
    """Rate limit decorator for account deletion endpoints."""
    if not settings.ENABLE_RATE_LIMITING:
        return _no_op_decorator(func)

    # Use slowapi's limit decorator
    return get_limiter().limit(settings.RATE_LIMIT_ACCOUNT_DELETION)(func)  # type: ignore[misc]


def rate_limit_custom(limit: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Custom rate limit decorator with specified limit."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        if not settings.ENABLE_RATE_LIMITING:
            return _no_op_decorator(func)

        # Use slowapi's limit decorator
        return get_limiter().limit(limit)(func)  # type: ignore[misc]

    return decorator


async def init_rate_limiter() -> None:
    """Initialize the rate limiter."""
    if settings.ENABLE_RATE_LIMITING:
        get_limiter()


def setup_rate_limiting(app: Any) -> None:
    """Setup rate limiting for the FastAPI app."""
    if not settings.ENABLE_RATE_LIMITING:
        return

    # Get the limiter instance
    limiter_instance = get_limiter()

    # Add rate limit exceeded handler
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Add limiter state to app state
    app.state.limiter = limiter_instance


class RateLimitInfoTD(TypedDict, total=False):
    enabled: bool
    client_ip: str
    remaining: int
    reset_time: int
    limit: int
    error: str


def get_rate_limit_info(request: Request) -> RateLimitInfoTD:
    """Get current rate limit information for the client."""
    if not settings.ENABLE_RATE_LIMITING:
        return {"enabled": False}

    try:
        client_ip = get_client_ip(request)

        # Get current limits for the client
        # Note: slowapi doesn't have get_window_stats, so we return basic info

    except Exception:
        # Return a fallback response if there's an error
        safe_client_ip = getattr(getattr(request, "client", None), "host", "unknown")
        return {
            "enabled": True,
            "error": "Failed to get rate limit information",
            "client_ip": safe_client_ip,
            "remaining": 0,
            "reset_time": 0,
            "limit": 0,
        }
    else:
        return {
            "enabled": True,
            "client_ip": client_ip,
            "remaining": 100,  # Default value
            "reset_time": 0,
            "limit": 100,  # Default value
        }
