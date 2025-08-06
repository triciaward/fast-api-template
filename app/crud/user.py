from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models import User
from app.schemas.user import UserCreate

# Type alias for both sync and async sessions
DBSession = AsyncSession | Session


def utc_now() -> datetime:
    """Get current UTC datetime (replaces deprecated datetime.utcnow())."""
    return datetime.now(UTC)


async def get_user_by_email(db: DBSession, email: str) -> User | None:
    if isinstance(db, AsyncSession):
        result = await db.execute(
            select(User).filter(User.email == email, User.is_deleted.is_(False))
        )
    else:
        result = db.execute(
            select(User).filter(User.email == email, User.is_deleted.is_(False))
        )
    return result.scalar_one_or_none()


async def get_user_by_username(db: DBSession, username: str) -> User | None:
    if isinstance(db, AsyncSession):
        result = await db.execute(
            select(User).filter(User.username == username, User.is_deleted.is_(False))
        )
    else:
        result = db.execute(
            select(User).filter(User.username == username, User.is_deleted.is_(False))
        )
    return result.scalar_one_or_none()


async def create_user(db: DBSession, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        is_superuser=user.is_superuser,
    )
    db.add(db_user)
    if isinstance(db, AsyncSession):
        await db.commit()
        try:
            await db.refresh(db_user)
        except Exception:
            pass
    else:
        db.commit()
        try:
            db.refresh(db_user)
        except Exception:
            pass
    return db_user


async def authenticate_user(db: DBSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, str(user.hashed_password)):
        return None
    return user


# Sync versions for testing and compatibility
def get_user_by_email_sync(db: Session, email: str) -> User | None:
    result = db.execute(
        select(User).filter(User.email == email, User.is_deleted.is_(False))
    )
    return result.scalar_one_or_none()


def get_user_by_username_sync(db: Session, username: str) -> User | None:
    result = db.execute(
        select(User).filter(User.username == username, User.is_deleted.is_(False))
    )
    return result.scalar_one_or_none()


def create_user_sync(db: Session, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        is_superuser=user.is_superuser,
    )
    db.add(db_user)
    db.commit()
    try:
        db.refresh(db_user)
    except Exception:
        pass
    return db_user


def authenticate_user_sync(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email_sync(db, email)
    if not user or not verify_password(password, str(user.hashed_password)):
        return None
    return user


# Additional user operations
def get_user_by_id_sync(db: Session, user_id: str) -> User | None:
    result = db.execute(
        select(User).filter(User.id == user_id, User.is_deleted.is_(False))
    )
    return result.scalar_one_or_none()


def get_user_by_oauth_id_sync(db: Session, provider: str, oauth_id: str) -> User | None:
    result = db.execute(
        select(User).filter(
            User.oauth_provider == provider,
            User.oauth_id == oauth_id,
            User.is_deleted.is_(False),
        )
    )
    return result.scalar_one_or_none()


def create_oauth_user_sync(
    db: Session,
    email: str,
    username: str,
    oauth_provider: str,
    oauth_id: str,
    oauth_email: str,
) -> User:
    db_user = User(
        email=email,
        username=username,
        oauth_provider=oauth_provider,
        oauth_id=oauth_id,
        oauth_email=oauth_email,
        is_verified=True,  # OAuth users are pre-verified
    )
    db.add(db_user)
    db.commit()
    try:
        db.refresh(db_user)
    except Exception:
        pass
    return db_user


def verify_user_sync(db: Session, user_id: str) -> bool:
    user = get_user_by_id_sync(db, user_id)
    if not user:
        return False

    user.is_verified = True  # type: ignore
    user.verification_token = None  # type: ignore
    user.verification_token_expires = None  # type: ignore

    db.commit()
    return True


def update_verification_token_sync(
    db: Session, user_id: str, token: str, expires: datetime
) -> bool:
    user = get_user_by_id_sync(db, user_id)
    if not user:
        return False

    user.verification_token = token  # type: ignore
    user.verification_token_expires = expires  # type: ignore

    db.commit()
    return True


def get_user_by_verification_token_sync(db: Session, token: str) -> User | None:
    result = db.execute(
        select(User).filter(
            User.verification_token == token,
            User.verification_token_expires > utc_now(),
            User.is_deleted.is_(False),
        )
    )
    return result.scalar_one_or_none()


def update_password_reset_token_sync(
    db: Session, user_id: str, token: str, expires: datetime
) -> bool:
    user = get_user_by_id_sync(db, user_id)
    if not user:
        return False

    user.password_reset_token = token  # type: ignore
    user.password_reset_token_expires = expires  # type: ignore

    db.commit()
    return True


def get_user_by_password_reset_token_sync(db: Session, token: str) -> User | None:
    result = db.execute(
        select(User).filter(
            User.password_reset_token == token,
            User.password_reset_token_expires > utc_now(),
            User.is_deleted.is_(False),
        )
    )
    return result.scalar_one_or_none()


def reset_user_password_sync(db: Session, user_id: str, new_password: str) -> bool:
    user = get_user_by_id_sync(db, user_id)
    if not user:
        return False

    user.hashed_password = get_password_hash(new_password)  # type: ignore
    user.password_reset_token = None  # type: ignore
    user.password_reset_token_expires = None  # type: ignore

    db.commit()
    return True


def update_user_password_sync(db: Session, user_id: str, new_password: str) -> bool:
    user = get_user_by_id_sync(db, user_id)
    if not user:
        return False

    user.hashed_password = get_password_hash(new_password)  # type: ignore

    db.commit()
    return True


def update_deletion_token_sync(
    db: Session, user_id: str, token: str, expires: datetime
) -> bool:
    user = get_user_by_id_sync(db, user_id)
    if not user:
        return False

    user.deletion_token = token  # type: ignore
    user.deletion_token_expires = expires  # type: ignore

    db.commit()
    return True


def get_user_by_deletion_token_sync(db: Session, token: str) -> User | None:
    result = db.execute(
        select(User).filter(
            User.deletion_token == token,
            User.deletion_token_expires > utc_now(),
            User.is_deleted.is_(False),
        )
    )
    return result.scalar_one_or_none()


def schedule_user_deletion_sync(
    db: Session, user_id: str, scheduled_date: datetime
) -> bool:
    user = get_user_by_id_sync(db, user_id)
    if not user:
        return False

    user.deletion_scheduled_for = scheduled_date  # type: ignore
    user.deletion_requested_at = utc_now()  # type: ignore

    db.commit()
    return True


def confirm_user_deletion_sync(db: Session, user_id: str) -> bool:
    user = get_user_by_id_sync(db, user_id)
    if not user:
        return False

    user.deletion_confirmed_at = utc_now()  # type: ignore

    db.commit()
    return True


def cancel_user_deletion_sync(db: Session, user_id: str) -> bool:
    user = get_user_by_id_sync(db, user_id)
    if not user:
        return False

    user.deletion_scheduled_for = None  # type: ignore
    user.deletion_requested_at = None  # type: ignore
    user.deletion_confirmed_at = None  # type: ignore
    user.deletion_token = None  # type: ignore
    user.deletion_token_expires = None  # type: ignore

    db.commit()
    return True


def get_users_for_deletion_reminder_sync(db: Session) -> list[User]:
    """Get users who need deletion reminders."""
    reminder_date = utc_now() + timedelta(days=1)
    result = db.execute(
        select(User).filter(
            User.deletion_scheduled_for <= reminder_date,
            User.deletion_scheduled_for > utc_now(),
            User.is_deleted.is_(False),
        )
    )
    return result.scalars().all()


def get_users_for_permanent_deletion_sync(db: Session) -> list[User]:
    """Get users who should be permanently deleted."""
    result = db.execute(
        select(User).filter(
            User.deletion_scheduled_for <= utc_now(), User.is_deleted.is_(False)
        )
    )
    return result.scalars().all()


def count_users_sync(db: Session) -> int:
    result = db.execute(select(User).filter(User.is_deleted.is_(False)))
    return len(result.scalars().all())


# Async versions of the new functions
async def get_user_by_id(db: DBSession, user_id: str) -> User | None:
    if isinstance(db, AsyncSession):
        result = await db.execute(
            select(User).filter(User.id == user_id, User.is_deleted.is_(False))
        )
    else:
        result = db.execute(
            select(User).filter(User.id == user_id, User.is_deleted.is_(False))
        )
    return result.scalar_one_or_none()


async def soft_delete_user(db: DBSession, user_id: str) -> bool:
    if isinstance(db, AsyncSession):
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
    else:
        result = db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()

    if not user:
        return False

    user.is_deleted = True  # type: ignore
    user.deleted_at = utc_now()  # type: ignore

    if isinstance(db, AsyncSession):
        await db.commit()
    else:
        db.commit()

    return True


async def restore_user(db: DBSession, user_id: str) -> bool:
    if isinstance(db, AsyncSession):
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
    else:
        result = db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()

    if not user:
        return False

    user.is_deleted = False  # type: ignore
    user.deleted_at = None  # type: ignore

    if isinstance(db, AsyncSession):
        await db.commit()
    else:
        db.commit()

    return True


async def permanently_delete_user(db: DBSession, user_id: str) -> bool:
    if isinstance(db, AsyncSession):
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
    else:
        result = db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()

    if not user:
        return False

    if isinstance(db, AsyncSession):
        await db.delete(user)
        await db.commit()
    else:
        db.delete(user)
        db.commit()

    return True


# Additional sync functions for testing compatibility
def cancel_account_deletion_sync(db: Session, user_id: str) -> bool:
    """Cancel account deletion (sync version)."""
    return cancel_user_deletion_sync(db, user_id)


def confirm_account_deletion_sync(db: Session, user_id: str) -> bool:
    """Confirm account deletion (sync version)."""
    return confirm_user_deletion_sync(db, user_id)


def request_account_deletion_sync(db: Session, user_id: str) -> bool:
    """Request account deletion (sync version)."""
    scheduled_date = utc_now() + timedelta(days=30)
    return schedule_user_deletion_sync(db, user_id, scheduled_date)


def get_user_by_id_any_status_sync(db: Session, user_id: str) -> User | None:
    """Get user by ID regardless of deletion status."""
    result = db.execute(select(User).filter(User.id == user_id))
    return result.scalar_one_or_none()


def soft_delete_user_sync(db: Session, user_id: str) -> bool:
    """Soft delete a user (sync version)."""
    user = get_user_by_id_sync(db, user_id)
    if not user:
        return False

    user.is_deleted = True  # type: ignore
    user.deleted_at = utc_now()  # type: ignore

    db.commit()
    return True


def restore_user_sync(db: Session, user_id: str) -> bool:
    """Restore a soft-deleted user (sync version)."""
    user = get_user_by_id_any_status_sync(db, user_id)
    if not user:
        return False

    user.is_deleted = False  # type: ignore
    user.deleted_at = None  # type: ignore

    db.commit()
    return True


def permanently_delete_user_sync(db: Session, user_id: str) -> bool:
    """Permanently delete a user (sync version)."""
    user = get_user_by_id_any_status_sync(db, user_id)
    if not user:
        return False

    db.delete(user)
    db.commit()
    return True


def get_deleted_users_sync(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    """Get deleted users (sync version)."""
    result = db.execute(
        select(User).filter(User.is_deleted.is_(True)).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


def count_deleted_users_sync(db: Session) -> int:
    """Count deleted users (sync version)."""
    result = db.execute(select(User).filter(User.is_deleted.is_(True)))
    return len(result.scalars().all())


def get_users_sync(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    """Get active users (sync version)."""
    result = db.execute(
        select(User).filter(User.is_deleted.is_(False)).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


# Async OAuth functions for compatibility
async def get_user_by_oauth_id(
    db: DBSession, oauth_provider: str, oauth_id: str
) -> User | None:
    """Get user by OAuth ID (async version)."""
    if isinstance(db, AsyncSession):
        result = await db.execute(
            select(User).filter(
                User.oauth_provider == oauth_provider,
                User.oauth_id == oauth_id,
                User.is_deleted.is_(False),
            )
        )
    else:
        result = db.execute(
            select(User).filter(
                User.oauth_provider == oauth_provider,
                User.oauth_id == oauth_id,
                User.is_deleted.is_(False),
            )
        )
    return result.scalar_one_or_none()


async def create_oauth_user(
    db: DBSession,
    email: str,
    username: str,
    oauth_provider: str,
    oauth_id: str,
    oauth_email: str,
) -> User:
    """Create OAuth user (async version)."""
    db_user = User(
        email=email,
        username=username,
        oauth_provider=oauth_provider,
        oauth_id=oauth_id,
        oauth_email=oauth_email,
        is_verified=True,  # OAuth users are pre-verified
    )
    db.add(db_user)
    if isinstance(db, AsyncSession):
        await db.commit()
        try:
            await db.refresh(db_user)
        except Exception:
            pass
    else:
        db.commit()
        try:
            db.refresh(db_user)
        except Exception:
            pass
    return db_user
