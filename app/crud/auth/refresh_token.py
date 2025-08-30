from datetime import datetime, timedelta
from typing import TypeAlias

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security.security import (
    fingerprint_refresh_token,
    hash_refresh_token,
    verify_refresh_token,
)
from app.models import RefreshToken
from app.utils.datetime_utils import utc_now

# Type alias for async sessions only
DBSession: TypeAlias = AsyncSession


async def create_refresh_token(
    db: DBSession,
    user_id: str,
    token_hash: str,
    device_info: str | None = None,
    ip_address: str | None = None,
) -> RefreshToken:
    """Create a new refresh token."""
    expires_at = utc_now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    # token_hash here is expected to be the HASH of the raw token
    # compute fingerprint from the corresponding raw token if provided as raw
    # However, since callers pass the raw token, compute hash+fingerprint here instead
    # If a hash is already passed, treat it as raw (legacy) and still compute correctly
    # Compute fingerprint from raw token and store hashed token
    raw_token = token_hash
    fingerprint = fingerprint_refresh_token(raw_token)
    hashed = hash_refresh_token(raw_token)

    refresh_token = RefreshToken()
    # Accept both str and UUID-like; store as-is to satisfy existing tests
    refresh_token.user_id = user_id  # type: ignore[assignment]
    refresh_token.token_hash = hashed
    refresh_token.token_fingerprint = fingerprint
    refresh_token.expires_at = expires_at
    refresh_token.device_info = device_info
    refresh_token.ip_address = ip_address

    db.add(refresh_token)
    await db.commit()
    try:
        await db.refresh(refresh_token)
    except SQLAlchemyError:
        pass

    return refresh_token


async def cleanup_expired_tokens(db: DBSession) -> int:
    """Clean up expired refresh tokens."""
    result = await db.execute(
        select(RefreshToken).filter(
            RefreshToken.expires_at < utc_now(),
            RefreshToken.is_revoked.is_(False),
        ),
    )
    expired_tokens = result.scalars().all()

    count = 0
    for token in expired_tokens:
        token.is_revoked = True
        count += 1

    await db.commit()
    return count


async def get_refresh_token_by_hash(
    db: DBSession,
    token_hash: str,
) -> RefreshToken | None:
    """Get refresh token by hash."""
    # This function is kept for backward-compat or administrative usage only.
    result = await db.execute(
        select(RefreshToken).filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.expires_at > utc_now(),
            RefreshToken.is_revoked.is_(False),
        ),
    )
    token: RefreshToken | None = result.scalar_one_or_none()
    return token


async def revoke_refresh_token(db: DBSession, token_hash: str) -> bool:
    """Revoke a refresh token."""
    token = await get_refresh_token_by_hash(db, token_hash)
    if not token:
        return False

    token.is_revoked = True
    await db.commit()

    return True


async def revoke_refresh_token_by_hash(db: DBSession, token_hash: str) -> bool:
    """Revoke a refresh token by hash."""
    return await revoke_refresh_token(db, token_hash)


async def revoke_refresh_token_by_id(db: DBSession, token_id: str) -> bool:
    """Revoke a refresh token by its database id."""
    result = await db.execute(
        select(RefreshToken).filter(RefreshToken.id == token_id),
    )
    token: RefreshToken | None = result.scalar_one_or_none()
    if not token:
        return False
    token.is_revoked = True
    await db.commit()
    return True


async def get_user_sessions(db: DBSession, user_id: str) -> list[RefreshToken]:
    """Get all active sessions for a user."""
    result = await db.execute(
        select(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.expires_at > utc_now(),
            RefreshToken.is_revoked.is_(False),
        ),
    )

    return list(result.scalars().all())


async def get_user_session_count(db: DBSession, user_id: str) -> int:
    """Get the number of active sessions for a user."""
    result = await db.execute(
        select(func.count())
        .select_from(RefreshToken)
        .filter(
            RefreshToken.user_id == user_id,
            RefreshToken.expires_at > utc_now(),
            RefreshToken.is_revoked.is_(False),
        ),
    )
    count: int = int(result.scalar() or 0)
    return count


async def revoke_all_user_sessions(db: DBSession, user_id: str) -> int:
    """Revoke all sessions for a user."""
    sessions = await get_user_sessions(db, user_id)

    for session in sessions:
        session.is_revoked = True

    await db.commit()
    return len(sessions)


async def verify_refresh_token_in_db(
    db: DBSession,
    token_hash: str,
) -> RefreshToken | None:
    """Verify a refresh token in the database.

    This takes a RAW token value, locates candidate by fingerprint, and verifies via bcrypt.
    """
    raw_token = token_hash
    fingerprint = fingerprint_refresh_token(raw_token)

    result = await db.execute(
        select(RefreshToken).filter(
            RefreshToken.token_fingerprint == fingerprint,
            RefreshToken.expires_at > utc_now(),
            RefreshToken.is_revoked.is_(False),
        ),
    )
    candidate: RefreshToken | None = result.scalar_one_or_none()
    if not candidate:
        # Backward compatibility: legacy records stored raw token in token_hash
        legacy_result = await db.execute(
            select(RefreshToken).filter(
                RefreshToken.token_hash == raw_token,
                RefreshToken.expires_at > utc_now(),
                RefreshToken.is_revoked.is_(False),
            ),
        )
        candidate = legacy_result.scalar_one_or_none()
        if not candidate:
            return None
        # Migrate legacy record in-place to hashed+fingerprint
        candidate.token_fingerprint = fingerprint
        candidate.token_hash = hash_refresh_token(raw_token)
        await db.commit()

    # Verify using bcrypt hash
    if not verify_refresh_token(raw_token, str(candidate.token_hash)):
        return None

    return candidate


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
            # created_at comes from TimestampMixin and is non-null
            return s.created_at

        sessions.sort(key=get_sort_key)

        # Revoke oldest sessions to reduce to max_sessions
        sessions_to_revoke = sessions[: max(0, len(sessions) - max_sessions)]

        for session in sessions_to_revoke:
            session.is_revoked = True

        await db.commit()
