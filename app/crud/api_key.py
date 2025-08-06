from datetime import datetime, timezone
from typing import Union

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.security import generate_api_key, hash_api_key, verify_api_key
from app.models import APIKey
from app.schemas.user import APIKeyCreate

# Type alias for both sync and async sessions
DBSession = Union[AsyncSession, Session]


def utc_now() -> datetime:
    """Get current UTC datetime (replaces deprecated datetime.utcnow())."""
    return datetime.now(timezone.utc)


async def create_api_key(
    db: DBSession,
    api_key_data: APIKeyCreate,
    user_id: str | None = None,
    raw_key: str = None,
) -> APIKey:
    """Create a new API key."""
    if raw_key is None:
        raw_key = generate_api_key()

    key_hash = hash_api_key(raw_key)

    db_api_key = APIKey(
        user_id=user_id,
        key_hash=key_hash,
        label=api_key_data.label,
        scopes=api_key_data.scopes,
        expires_at=api_key_data.expires_at,
    )

    db.add(db_api_key)
    if isinstance(db, AsyncSession):
        await db.commit()
        try:
            await db.refresh(db_api_key)
        except Exception:
            pass
    else:
        db.commit()
        try:
            db.refresh(db_api_key)
        except Exception:
            pass

    return db_api_key


async def get_api_key_by_hash(db: DBSession, key_hash: str) -> APIKey | None:
    """Get API key by hash."""
    if isinstance(db, AsyncSession):
        result = await db.execute(
            select(APIKey).filter(
                APIKey.key_hash == key_hash,
                APIKey.is_deleted.is_(False),
            )
        )
    else:
        result = db.execute(
            select(APIKey).filter(
                APIKey.key_hash == key_hash,
                APIKey.is_deleted.is_(False),
            )
        )

    return result.scalar_one_or_none()


async def verify_api_key_in_db(db: DBSession, raw_key: str) -> APIKey | None:
    """Verify an API key against the database."""
    # Get all non-deleted API keys (regardless of status)
    if isinstance(db, AsyncSession):
        result = await db.execute(select(APIKey).filter(APIKey.is_deleted.is_(False)))
    else:
        result = db.execute(select(APIKey).filter(APIKey.is_deleted.is_(False)))
    api_keys = result.scalars().all()

    # Check each key to see if the raw key matches
    for api_key in api_keys:
        assert api_key.key_hash is not None  # type: ignore
        if verify_api_key(raw_key, api_key.key_hash):  # type: ignore
            # Found the key, now check if it's active and not expired
            if not api_key.is_active:
                # Return the key so the caller can check is_active and raise appropriate error
                return api_key
            if api_key.expires_at and api_key.expires_at <= utc_now():
                # Return the key so the caller can check expires_at and raise appropriate error
                return api_key
            # Key is valid
            return api_key

    return None


async def get_user_api_keys(
    db: DBSession, user_id: str, skip: int = 0, limit: int = 100
) -> list[APIKey]:
    """Get all API keys for a user."""
    if isinstance(db, AsyncSession):
        result = await db.execute(
            select(APIKey)
            .filter(
                APIKey.user_id == user_id,
                APIKey.is_deleted.is_(False),
            )
            .offset(skip)
            .limit(limit)
        )
    else:
        result = db.execute(
            select(APIKey)
            .filter(
                APIKey.user_id == user_id,
                APIKey.is_deleted.is_(False),
            )
            .offset(skip)
            .limit(limit)
        )

    return result.scalars().all()


async def count_user_api_keys(db: DBSession, user_id: str) -> int:
    """Count API keys for a user."""
    if isinstance(db, AsyncSession):
        result = await db.execute(
            select(APIKey).filter(
                and_(APIKey.user_id == user_id, APIKey.is_deleted.is_(False))
            )
        )
    else:
        result = db.execute(
            select(APIKey).filter(
                and_(APIKey.user_id == user_id, APIKey.is_deleted.is_(False))
            )
        )
    return len(result.scalars().all())


async def get_api_key_by_id(
    db: DBSession, key_id: str, user_id: str | None = None
) -> APIKey | None:
    """Get API key by ID, optionally filtering by user."""
    query = select(APIKey).filter(
        and_(APIKey.id == key_id, APIKey.is_deleted.is_(False))
    )

    if user_id:
        query = query.filter(APIKey.user_id == user_id)

    if isinstance(db, AsyncSession):
        result = await db.execute(query)
    else:
        result = db.execute(query)
    return result.scalar_one_or_none()


async def deactivate_api_key(
    db: DBSession, key_id: str, user_id: str | None = None
) -> bool:
    """Deactivate an API key."""
    api_key = await get_api_key_by_id(db, key_id, user_id)
    if not api_key:
        return False

    api_key.is_active = False  # type: ignore
    if isinstance(db, AsyncSession):
        await db.commit()
    else:
        db.commit()

    return True


async def rotate_api_key(
    db: DBSession, key_id: str, user_id: str | None = None
) -> tuple[APIKey | None, str | None]:
    """Rotate an API key by generating a new one and deactivating the old one."""
    api_key = await get_api_key_by_id(db, key_id, user_id)
    if not api_key:
        return None, None

    # Generate new key
    new_raw_key = generate_api_key()
    new_key_hash = hash_api_key(new_raw_key)

    # Update the existing key
    api_key.key_hash = new_key_hash  # type: ignore
    api_key.is_active = True  # type: ignore

    if isinstance(db, AsyncSession):
        await db.commit()
        try:
            await db.refresh(api_key)
        except Exception:
            pass
    else:
        db.commit()
        try:
            db.refresh(api_key)
        except Exception:
            pass

    return api_key, new_raw_key


# Sync versions for compatibility
def create_api_key_sync(
    db: Session,
    api_key_data: APIKeyCreate,
    user_id: str | None = None,
    raw_key: str = None,
) -> APIKey:
    """Create a new API key (sync version)."""
    if raw_key is None:
        raw_key = generate_api_key()

    key_hash = hash_api_key(raw_key)

    db_api_key = APIKey(
        user_id=user_id,
        key_hash=key_hash,
        label=api_key_data.label,
        scopes=api_key_data.scopes,
        expires_at=api_key_data.expires_at,
    )

    db.add(db_api_key)
    db.commit()
    try:
        db.refresh(db_api_key)
    except Exception:
        pass

    return db_api_key


def get_api_key_by_hash_sync(db: Session, key_hash: str) -> APIKey | None:
    """Get API key by its hash (sync version)."""
    result = db.execute(
        select(APIKey).filter(
            and_(
                APIKey.key_hash == key_hash,
                APIKey.is_active.is_(True),
                APIKey.is_deleted.is_(False),
                (APIKey.expires_at.is_(None) | (APIKey.expires_at > utc_now())),
            )
        )
    )
    return result.scalar_one_or_none()


def verify_api_key_in_db_sync(db: Session, raw_key: str) -> APIKey | None:
    """Verify an API key against the database (sync version)."""
    # Get all non-deleted API keys (regardless of status)
    result = db.execute(select(APIKey).filter(APIKey.is_deleted.is_(False)))
    api_keys = result.scalars().all()

    # Check each key to see if the raw key matches
    for api_key in api_keys:
        assert api_key.key_hash is not None  # type: ignore
        if verify_api_key(raw_key, api_key.key_hash):  # type: ignore
            # Found the key, now check if it's active and not expired
            if not api_key.is_active:
                # Return the key so the caller can check is_active and raise appropriate error
                return api_key
            if api_key.expires_at and api_key.expires_at <= utc_now():
                # Return the key so the caller can check expires_at and raise appropriate error
                return api_key
            # Key is valid
            return api_key

    return None


def get_user_api_keys_sync(
    db: Session, user_id: str, skip: int = 0, limit: int = 100
) -> list[APIKey]:
    """Get all API keys for a user (sync version)."""
    result = db.execute(
        select(APIKey)
        .filter(and_(APIKey.user_id == user_id, APIKey.is_deleted.is_(False)))
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


def count_user_api_keys_sync(db: Session, user_id: str) -> int:
    """Count API keys for a user (sync version)."""
    result = db.execute(
        select(APIKey).filter(
            and_(APIKey.user_id == user_id, APIKey.is_deleted.is_(False))
        )
    )
    return len(result.scalars().all())


def get_api_key_by_id_sync(
    db: Session, key_id: str, user_id: str | None = None
) -> APIKey | None:
    """Get API key by ID, optionally filtering by user (sync version)."""
    query = select(APIKey).filter(
        and_(APIKey.id == key_id, APIKey.is_deleted.is_(False))
    )

    if user_id:
        query = query.filter(APIKey.user_id == user_id)

    result = db.execute(query)
    return result.scalar_one_or_none()


def deactivate_api_key_sync(
    db: Session, key_id: str, user_id: str | None = None
) -> bool:
    """Deactivate an API key (sync version)."""
    api_key = get_api_key_by_id_sync(db, key_id, user_id)
    if not api_key:
        return False

    api_key.is_active = False  # type: ignore
    db.commit()

    return True


def rotate_api_key_sync(
    db: Session, key_id: str, user_id: str | None = None
) -> tuple[APIKey | None, str | None]:
    """Rotate an API key by generating a new one and deactivating the old one (sync version)."""
    api_key = get_api_key_by_id_sync(db, key_id, user_id)
    if not api_key:
        return None, None

    # Generate new key
    new_raw_key = generate_api_key()
    new_key_hash = hash_api_key(new_raw_key)

    # Update the existing key
    api_key.key_hash = new_key_hash  # type: ignore
    api_key.is_active = True  # type: ignore

    db.commit()
    try:
        db.refresh(api_key)
    except Exception:
        pass

    return api_key, new_raw_key


def get_all_api_keys_sync(db: Session, skip: int = 0, limit: int = 100) -> list[APIKey]:
    """Get all API keys in the system (admin only, sync version)."""
    result = db.execute(
        select(APIKey)
        .filter(APIKey.is_deleted.is_(False))
        .order_by(APIKey.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


def count_all_api_keys_sync(db: Session) -> int:
    """Count all API keys in the system (admin only, sync version)."""
    result = db.execute(select(APIKey).filter(APIKey.is_deleted.is_(False)))
    return len(result.scalars().all())
