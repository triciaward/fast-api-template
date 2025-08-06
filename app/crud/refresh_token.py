from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import RefreshToken

# Type alias for both sync and async sessions
DBSession = AsyncSession | Session


def utc_now() -> datetime:
    """Get current UTC datetime (replaces deprecated datetime.utcnow())."""
    return datetime.now(timezone.utc)


async def create_refresh_token(
    db: DBSession,
    user_id: str,
    token_hash: str,
    device_info: str | None = None,
    ip_address: str | None = None,
) -> RefreshToken:
    """Create a new refresh token."""
    expires_at = utc_now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        device_info=device_info,
        ip_address=ip_address,
    )

    db.add(refresh_token)
    if isinstance(db, AsyncSession):
        await db.commit()
        try:
            await db.refresh(refresh_token)
        except Exception:
            pass
    else:
        db.commit()
        try:
            db.refresh(refresh_token)
        except Exception:
            pass

    return refresh_token


async def cleanup_expired_tokens(db: DBSession) -> int:
    """Clean up expired refresh tokens."""
    if isinstance(db, AsyncSession):
        result = await db.execute(
            select(RefreshToken).filter(
                RefreshToken.expires_at > utc_now(),
                RefreshToken.is_revoked.is_(False),
            ),
        )
        expired_tokens = result.scalars().all()
    else:
        result = db.execute(
            select(RefreshToken).filter(
                RefreshToken.expires_at > utc_now(),
                RefreshToken.is_revoked.is_(False),
            ),
        )
        expired_tokens = result.scalars().all()

    count = 0
    for token in expired_tokens:
        token.is_revoked = True  # type: ignore
        count += 1

    if isinstance(db, AsyncSession):
        await db.commit()
    else:
        db.commit()

    return count


async def get_refresh_token_by_hash(
    db: DBSession,
    token_hash: str,
) -> RefreshToken | None:
    """Get refresh token by hash."""
    if isinstance(db, AsyncSession):
        result = await db.execute(
            select(RefreshToken).filter(
                RefreshToken.token_hash == token_hash,
                RefreshToken.expires_at > utc_now(),
                RefreshToken.is_revoked.is_(False),
            ),
        )
    else:
        result = db.execute(
            select(RefreshToken).filter(
                RefreshToken.token_hash == token_hash,
                RefreshToken.expires_at > utc_now(),
                RefreshToken.is_revoked.is_(False),
            ),
        )

    return result.scalar_one_or_none()


async def revoke_refresh_token(db: DBSession, token_hash: str) -> bool:
    """Revoke a refresh token."""
    token = await get_refresh_token_by_hash(db, token_hash)
    if not token:
        return False

    token.is_revoked = True  # type: ignore

    if isinstance(db, AsyncSession):
        await db.commit()
    else:
        db.commit()

    return True


async def revoke_refresh_token_by_hash(db: DBSession, token_hash: str) -> bool:
    """Revoke a refresh token by hash."""
    return await revoke_refresh_token(db, token_hash)


async def get_user_sessions(db: DBSession, user_id: str) -> list[RefreshToken]:
    """Get all active sessions for a user."""
    if isinstance(db, AsyncSession):
        result = await db.execute(
            select(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.expires_at > utc_now(),
                RefreshToken.is_revoked.is_(False),
            ),
        )
    else:
        result = db.execute(
            select(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.expires_at > utc_now(),
                RefreshToken.is_revoked.is_(False),
            ),
        )

    return list(result.scalars().all())


async def get_user_session_count(db: DBSession, user_id: str) -> int:
    """Get the number of active sessions for a user."""
    sessions = await get_user_sessions(db, user_id)
    return len(sessions)


async def revoke_all_user_sessions(db: DBSession, user_id: str) -> int:
    """Revoke all sessions for a user."""
    sessions = await get_user_sessions(db, user_id)
    count = 0

    for session in sessions:
        session.is_revoked = True  # type: ignore
        count += 1

    if isinstance(db, AsyncSession):
        await db.commit()
    else:
        db.commit()

    return count


async def verify_refresh_token_in_db(
    db: DBSession,
    token_hash: str,
) -> RefreshToken | None:
    """Verify a refresh token in the database."""
    return await get_refresh_token_by_hash(db, token_hash)


async def enforce_session_limit(
    db: DBSession,
    user_id: str,
    max_sessions: int = 5,
) -> None:
    """Enforce session limit by revoking oldest sessions if needed."""
    sessions = await get_user_sessions(db, user_id)

    if len(sessions) >= max_sessions:
        # Sort by creation date (oldest first)
        def get_sort_key(s: RefreshToken) -> datetime:
            return s.created_at if s.created_at is not None else utc_now()  # type: ignore

        sessions.sort(key=get_sort_key)

        # Revoke oldest sessions to stay under limit
        sessions_to_revoke = sessions[: -max_sessions + 1]

        for session in sessions_to_revoke:
            session.is_revoked = True  # type: ignore

        if isinstance(db, AsyncSession):
            await db.commit()
        else:
            db.commit()
