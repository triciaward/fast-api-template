from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.security import get_password_hash, verify_password
from app.models import User
from app.schemas.auth.user import UserCreate
from app.utils.datetime_utils import utc_now

# Type alias for async sessions only
DBSession = AsyncSession


async def get_user_by_email(db: DBSession, email: str) -> User | None:
    result = await db.execute(
        select(User).filter(User.email == email, User.is_deleted.is_(False)),
    )
    return result.scalar_one_or_none()


async def get_user_by_username(db: DBSession, username: str) -> User | None:
    result = await db.execute(
        select(User).filter(User.username == username, User.is_deleted.is_(False)),
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
    await db.commit()
    try:
        await db.refresh(db_user)
    except Exception:
        pass
    return db_user


async def authenticate_user(db: DBSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, str(user.hashed_password)):
        return None
    return user


async def get_user_by_id(db: DBSession, user_id: str) -> User | None:
    result = await db.execute(
        select(User).filter(User.id == user_id, User.is_deleted.is_(False)),
    )
    return result.scalar_one_or_none()


async def get_user_by_oauth_id(
    db: DBSession,
    oauth_provider: str,
    oauth_id: str,
) -> User | None:
    result = await db.execute(
        select(User).filter(
            User.oauth_provider == oauth_provider,
            User.oauth_id == oauth_id,
            User.is_deleted.is_(False),
        ),
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
    db_user = User(
        email=email,
        username=username,
        oauth_provider=oauth_provider,
        oauth_id=oauth_id,
        oauth_email=oauth_email,
        is_verified=True,  # OAuth users are pre-verified
    )
    db.add(db_user)
    await db.commit()
    try:
        await db.refresh(db_user)
    except Exception:
        pass
    return db_user


async def verify_user(db: DBSession, user_id: str) -> bool:
    user = await get_user_by_id(db, user_id)
    if not user:
        return False

    user.is_verified = True  # type: ignore
    user.verification_token = None  # type: ignore
    user.verification_token_expires = None  # type: ignore

    await db.commit()
    return True


async def update_verification_token(
    db: DBSession,
    user_id: str,
    token: str,
    expires: datetime,
) -> bool:
    user = await get_user_by_id(db, user_id)
    if not user:
        return False

    user.verification_token = token  # type: ignore
    user.verification_token_expires = expires  # type: ignore

    await db.commit()
    return True


async def get_user_by_verification_token(db: DBSession, token: str) -> User | None:
    result = await db.execute(
        select(User).filter(
            User.verification_token == token,
            User.verification_token_expires > utc_now(),
            User.is_deleted.is_(False),
        ),
    )
    return result.scalar_one_or_none()


async def update_password_reset_token(
    db: DBSession,
    user_id: str,
    token: str,
    expires: datetime,
) -> bool:
    user = await get_user_by_id(db, user_id)
    if not user:
        return False

    user.password_reset_token = token  # type: ignore
    user.password_reset_token_expires = expires  # type: ignore

    await db.commit()
    return True


async def get_user_by_password_reset_token(db: DBSession, token: str) -> User | None:
    result = await db.execute(
        select(User).filter(
            User.password_reset_token == token,
            User.password_reset_token_expires > utc_now(),
            User.is_deleted.is_(False),
        ),
    )
    return result.scalar_one_or_none()


async def reset_user_password(db: DBSession, user_id: str, new_password: str) -> bool:
    user = await get_user_by_id(db, user_id)
    if not user:
        return False

    user.hashed_password = get_password_hash(new_password)  # type: ignore
    user.password_reset_token = None  # type: ignore
    user.password_reset_token_expires = None  # type: ignore

    await db.commit()
    return True


async def update_user_password(db: DBSession, user_id: str, new_password: str) -> bool:
    user = await get_user_by_id(db, user_id)
    if not user:
        return False

    user.hashed_password = get_password_hash(new_password)  # type: ignore

    await db.commit()
    return True


async def update_deletion_token(
    db: DBSession,
    user_id: str,
    token: str,
    expires: datetime,
) -> bool:
    user = await get_user_by_id(db, user_id)
    if not user:
        return False

    user.deletion_token = token  # type: ignore
    user.deletion_token_expires = expires  # type: ignore

    await db.commit()
    return True


async def get_user_by_deletion_token(db: DBSession, token: str) -> User | None:
    result = await db.execute(
        select(User).filter(
            User.deletion_token == token,
            User.deletion_token_expires > utc_now(),
            User.is_deleted.is_(False),
        ),
    )
    return result.scalar_one_or_none()


async def schedule_user_deletion(
    db: DBSession,
    user_id: str,
    scheduled_date: datetime,
) -> bool:
    user = await get_user_by_id(db, user_id)
    if not user:
        return False

    user.deletion_scheduled_for = scheduled_date  # type: ignore[assignment]
    user.deletion_requested_at = utc_now()  # type: ignore[assignment]

    await db.commit()
    return True


async def confirm_user_deletion(db: DBSession, user_id: str) -> bool:
    user = await get_user_by_id(db, user_id)
    if not user:
        return False

    user.is_deleted = True  # type: ignore[assignment]
    user.deleted_at = utc_now()  # type: ignore[assignment]
    user.deletion_scheduled_for = None  # type: ignore[assignment]
    user.deletion_requested_at = None  # type: ignore[assignment]
    user.deletion_confirmed_at = utc_now()  # type: ignore[assignment]
    user.deletion_token = None  # type: ignore[assignment]
    user.deletion_token_expires = None  # type: ignore[assignment]

    await db.commit()
    return True


async def cancel_user_deletion(db: DBSession, user_id: str) -> bool:
    user = await get_user_by_id(db, user_id)
    if not user:
        return False

    user.deletion_scheduled_for = None  # type: ignore[assignment]
    user.deletion_requested_at = None  # type: ignore[assignment]
    user.deletion_confirmed_at = None  # type: ignore[assignment]
    user.deletion_token = None  # type: ignore[assignment]
    user.deletion_token_expires = None  # type: ignore[assignment]

    await db.commit()
    return True


async def get_users_for_deletion_reminder(db: DBSession) -> list[User]:
    """Get users who have requested deletion and need reminders."""
    reminder_date = utc_now() + timedelta(days=7)
    result = await db.execute(
        select(User).filter(
            User.is_deletion_requested.is_(True),
            User.deletion_scheduled_date <= reminder_date,
            User.is_deleted.is_(False),
        ),
    )
    return list(result.scalars().all())


async def get_users_for_permanent_deletion(db: DBSession) -> list[User]:
    """Get users who should be permanently deleted."""
    deletion_date = utc_now() - timedelta(days=30)
    result = await db.execute(
        select(User).filter(
            User.is_deleted.is_(True),
            User.deleted_at <= deletion_date,
        ),
    )
    return list(result.scalars().all())


async def count_users(db: DBSession) -> int:
    """Count all non-deleted users."""
    result = await db.execute(
        select(User).filter(User.is_deleted.is_(False)),
    )
    return len(result.scalars().all())


async def soft_delete_user(db: DBSession, user_id: str) -> bool:
    user = await get_user_by_id(db, user_id)
    if not user:
        return False

    user.is_deleted = True  # type: ignore[assignment]
    user.deleted_at = utc_now()  # type: ignore[assignment]

    await db.commit()
    return True


async def restore_user(db: DBSession, user_id: str) -> bool:
    user = await get_user_by_id_any_status(db, user_id)
    if not user or not user.is_deleted:
        return False

    user.is_deleted = False  # type: ignore
    user.deleted_at = None  # type: ignore

    await db.commit()
    return True


async def permanently_delete_user(db: DBSession, user_id: str) -> bool:
    user = await get_user_by_id_any_status(db, user_id)
    if not user:
        return False

    await db.delete(user)
    await db.commit()
    return True


async def cancel_account_deletion(db: DBSession, user_id: str) -> bool:
    return await cancel_user_deletion(db, user_id)


async def confirm_account_deletion(db: DBSession, user_id: str) -> bool:
    return await confirm_user_deletion(db, user_id)


async def request_account_deletion(db: DBSession, user_id: str) -> bool:
    return await schedule_user_deletion(db, user_id, utc_now() + timedelta(days=30))


async def get_user_by_id_any_status(db: DBSession, user_id: str) -> User | None:
    """Get user by ID regardless of deletion status."""
    result = await db.execute(
        select(User).filter(User.id == user_id),
    )
    return result.scalar_one_or_none()


async def get_deleted_users(
    db: DBSession, skip: int = 0, limit: int = 100
) -> list[User]:
    """Get list of deleted users."""
    result = await db.execute(
        select(User).filter(User.is_deleted.is_(True)).offset(skip).limit(limit),
    )
    return list(result.scalars().all())


async def count_deleted_users(db: DBSession) -> int:
    """Count all deleted users."""
    result = await db.execute(
        select(User).filter(User.is_deleted.is_(True)),
    )
    return len(result.scalars().all())


async def get_users(db: DBSession, skip: int = 0, limit: int = 100) -> list[User]:
    """Get list of non-deleted users."""
    result = await db.execute(
        select(User).filter(User.is_deleted.is_(False)).offset(skip).limit(limit),
    )
    return list(result.scalars().all())
