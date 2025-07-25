import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_refresh_token, verify_refresh_token
from app.models import RefreshToken


def create_refresh_token(
    db: Session,
    user_id: uuid.UUID,
    token: str,
    device_info: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> RefreshToken:
    """Create a new refresh token for a user."""
    token_hash = hash_refresh_token(token)
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    db_refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        device_info=device_info,
        ip_address=ip_address,
    )

    db.add(db_refresh_token)
    db.commit()
    db.refresh(db_refresh_token)
    return db_refresh_token


def get_refresh_token_by_hash(db: Session, token_hash: str) -> Optional[RefreshToken]:
    """Get a refresh token by its hash."""
    # This function is deprecated - use verify_refresh_token_in_db instead
    # because bcrypt generates different hashes for the same input
    return None


def verify_refresh_token_in_db(db: Session, token: str) -> Optional[RefreshToken]:
    """Verify a refresh token against the database."""
    # Get all active tokens and verify each one
    # This is necessary because bcrypt generates different hashes for the same input
    active_tokens = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.is_revoked == False,  # noqa: E712
            RefreshToken.expires_at > datetime.utcnow(),
        )
        .all()
    )

    for db_token in active_tokens:
        if verify_refresh_token(token, str(db_token.token_hash)):
            return db_token

    return None


def revoke_refresh_token(db: Session, token_id: uuid.UUID) -> bool:
    """Revoke a specific refresh token."""
    db_token = db.query(RefreshToken).filter(RefreshToken.id == token_id).first()
    if db_token:
        db_token.is_revoked = True  # type: ignore
        db.commit()
        return True
    return False


def revoke_refresh_token_by_hash(db: Session, token_hash: str) -> bool:
    """Revoke a refresh token by its hash."""
    # This function is deprecated - use revoke_session instead
    # because bcrypt generates different hashes for the same input
    return False


def revoke_all_user_sessions(
    db: Session, user_id: uuid.UUID, except_token_id: Optional[uuid.UUID] = None
) -> int:
    """Revoke all refresh tokens for a user, optionally excepting one."""
    query = db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.is_revoked == False,  # noqa: E712
    )

    if except_token_id:
        query = query.filter(RefreshToken.id != except_token_id)

    revoked_count = query.update({"is_revoked": True})
    db.commit()
    return revoked_count


def get_user_sessions(
    db: Session, user_id: uuid.UUID, current_token_id: Optional[uuid.UUID] = None
) -> list[RefreshToken]:
    """Get all active sessions for a user."""
    query = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False,  # noqa: E712
            RefreshToken.expires_at > datetime.utcnow(),
        )
        .order_by(RefreshToken.created_at.desc())
    )

    sessions = query.all()

    # Mark current session if provided
    if current_token_id:
        for session in sessions:
            if session.id == current_token_id:
                session.is_current = True  # type: ignore
                break

    return sessions


def get_user_session_count(db: Session, user_id: uuid.UUID) -> int:
    """Get the count of active sessions for a user."""
    return (
        db.query(RefreshToken)
        .filter(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False,  # noqa: E712
            RefreshToken.expires_at > datetime.utcnow(),
        )
        .count()
    )


def cleanup_expired_tokens(db: Session) -> int:
    """Remove expired refresh tokens from the database."""
    deleted_count = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.expires_at <= datetime.utcnow(),
        )
        .delete()
    )
    db.commit()
    return deleted_count


def enforce_session_limit(
    db: Session, user_id: uuid.UUID, new_token_id: uuid.UUID
) -> None:
    """Enforce the maximum sessions per user limit by revoking oldest sessions."""
    active_sessions = get_user_sessions(db, user_id, new_token_id)

    if len(active_sessions) > settings.MAX_SESSIONS_PER_USER:
        # Sort by creation date (oldest first) and revoke excess sessions
        sessions_to_revoke = active_sessions[settings.MAX_SESSIONS_PER_USER :]
        for session in sessions_to_revoke:
            revoke_refresh_token(db, session.id)  # type: ignore
