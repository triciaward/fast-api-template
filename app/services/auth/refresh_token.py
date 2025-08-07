import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security.security import create_access_token
from app.core.security.security import (
    create_refresh_token as create_refresh_token_value,
)
from app.crud import (
    create_refresh_token as crud_create_refresh_token,
)
from app.crud import (
    enforce_session_limit,
    verify_refresh_token_in_db,
)
from app.models import User


def utc_now() -> datetime:
    """Get current UTC datetime (replaces deprecated datetime.utcnow())."""
    return datetime.now(timezone.utc)


def get_device_info(request: Request) -> str:
    """Extract device information from request headers."""
    user_agent = request.headers.get("user-agent", "Unknown")
    # Extract basic device info (browser, OS, etc.)
    if "Mozilla" in user_agent:
        if "Chrome" in user_agent:
            browser = "Chrome"
        elif "Firefox" in user_agent:
            browser = "Firefox"
        elif "Safari" in user_agent:
            browser = "Safari"
        else:
            browser = "Other"

        if "Windows" in user_agent:
            os = "Windows"
        elif "Mac" in user_agent:
            os = "macOS"
        elif "Linux" in user_agent:
            os = "Linux"
        elif "Android" in user_agent:
            os = "Android"
        elif "iPhone" in user_agent or "iPad" in user_agent:
            os = "iOS"
        else:
            os = "Other"

        return f"{browser} on {os}"

    return "Unknown Device"


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    # Check for forwarded headers (common with proxies/load balancers)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip

    return request.client.host if request.client else "unknown"


def set_refresh_token_cookie(response: Response, token: str) -> None:
    """Set the refresh token as an HttpOnly cookie."""
    response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        value=token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS
        * 24
        * 60
        * 60,  # Convert days to seconds
        httponly=settings.REFRESH_TOKEN_COOKIE_HTTPONLY,
        secure=settings.REFRESH_TOKEN_COOKIE_SECURE,
        samesite=settings.REFRESH_TOKEN_COOKIE_SAMESITE,  # type: ignore
        path=settings.REFRESH_TOKEN_COOKIE_PATH,
    )


def clear_refresh_token_cookie(response: Response) -> None:
    """Clear the refresh token cookie."""
    response.delete_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        path=settings.REFRESH_TOKEN_COOKIE_PATH,
    )


def get_refresh_token_from_cookie(request: Request) -> str | None:
    """Get the refresh token from the request cookies."""
    return request.cookies.get(settings.REFRESH_TOKEN_COOKIE_NAME)


async def create_user_session(
    db: AsyncSession,
    user: User,
    request: Request,
) -> tuple[str, str]:
    """Create a new user session with access and refresh tokens."""
    # Create refresh token
    refresh_token_value = create_refresh_token_value()

    # Get device info and IP
    device_info = get_device_info(request)
    ip_address = get_client_ip(request)

    # Store refresh token in database
    await crud_create_refresh_token(
        db=db,
        user_id=user.id,  # type: ignore
        token_hash=refresh_token_value,
        device_info=device_info,
        ip_address=ip_address,
    )

    # Enforce session limit
    await enforce_session_limit(db, user.id, 5)  # type: ignore

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.email,
        expires_delta=access_token_expires,
    )

    return access_token, refresh_token_value


async def refresh_access_token(
    db: AsyncSession,
    refresh_token_value: str,
) -> tuple[str, datetime] | None:
    """Refresh an access token using a valid refresh token."""
    # Verify refresh token
    db_refresh_token = await verify_refresh_token_in_db(db, refresh_token_value)
    if not db_refresh_token:
        return None

    # Get user
    from sqlalchemy import select

    result = await db.execute(select(User).filter(User.id == db_refresh_token.user_id))
    user = result.scalar_one_or_none()
    if not user or user.is_deleted:
        return None

    # Create new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.email,
        expires_delta=access_token_expires,
    )

    # Calculate expiration time
    expires_at = utc_now() + access_token_expires

    return access_token, expires_at


async def revoke_session(
    db: AsyncSession,
    refresh_token_value: str,
) -> bool:
    """Revoke a specific session by refresh token."""
    # Find the token using verification
    db_refresh_token = await verify_refresh_token_in_db(db, refresh_token_value)
    if not db_refresh_token:
        return False

    # Revoke the token
    from app.crud import revoke_refresh_token

    return await revoke_refresh_token(db, str(db_refresh_token.id))


async def revoke_all_sessions(
    db: AsyncSession,
    user_id: uuid.UUID,
    except_token_value: str | None = None,
) -> int:
    """Revoke all sessions for a user, optionally excepting one."""
    from app.core.security.security import hash_refresh_token
    from app.crud import revoke_all_user_sessions

    if except_token_value:
        token_hash = hash_refresh_token(except_token_value)
        from app.crud import get_refresh_token_by_hash

        db_token = await get_refresh_token_by_hash(db, token_hash)
        if db_token:
            # Note: except_token_id is not currently used in the CRUD function
            # but kept for future implementation
            _except_token_id = uuid.UUID(str(db_token.id))

    return await revoke_all_user_sessions(db, str(user_id))
