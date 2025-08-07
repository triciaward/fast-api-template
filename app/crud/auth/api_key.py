from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.security import generate_api_key, hash_api_key, verify_api_key
from app.models import APIKey
from app.schemas.auth.user import APIKeyCreate
from app.utils.datetime_utils import utc_now

# Type alias for async sessions only
DBSession = AsyncSession


async def create_api_key(
    db: DBSession,
    api_key_data: APIKeyCreate,
    user_id: str | None = None,
    raw_key: str | None = None,
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
    await db.commit()
    try:
        await db.refresh(db_api_key)
    except Exception:
        pass

    return db_api_key


async def get_api_key_by_hash(db: DBSession, key_hash: str) -> APIKey | None:
    """Get API key by hash."""
    result = await db.execute(
        select(APIKey).filter(
            APIKey.key_hash == key_hash,
            APIKey.is_deleted.is_(False),
        ),
    )

    return result.scalar_one_or_none()


async def verify_api_key_in_db(db: DBSession, raw_key: str) -> APIKey | None:
    """Verify an API key against the database."""
    # Get all non-deleted API keys (regardless of status)
    result = await db.execute(select(APIKey).filter(APIKey.is_deleted.is_(False)))
    api_keys = result.scalars().all()

    # Check each key to see if the raw key matches
    for api_key in api_keys:
        assert api_key.key_hash is not None
        if verify_api_key(raw_key, api_key.key_hash):  # type: ignore[arg-type]
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
    db: DBSession,
    user_id: str,
    skip: int = 0,
    limit: int = 100,
) -> list[APIKey]:
    """Get all API keys for a user."""
    result = await db.execute(
        select(APIKey)
        .filter(
            and_(
                APIKey.user_id == user_id,
                APIKey.is_deleted.is_(False),
            ),
        )
        .order_by(APIKey.created_at.desc())
        .offset(skip)
        .limit(limit),
    )

    return list(result.scalars().all())


async def count_user_api_keys(db: DBSession, user_id: str) -> int:
    """Count API keys for a user."""
    result = await db.execute(
        select(APIKey).filter(
            and_(
                APIKey.user_id == user_id,
                APIKey.is_deleted.is_(False),
            ),
        ),
    )
    return len(result.scalars().all())


async def get_api_key_by_id(
    db: DBSession,
    key_id: str,
    user_id: str | None = None,
) -> APIKey | None:
    """Get API key by ID."""
    query = select(APIKey).filter(
        and_(
            APIKey.id == key_id,
            APIKey.is_deleted.is_(False),
        ),
    )

    if user_id is not None:
        query = query.filter(APIKey.user_id == user_id)

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def deactivate_api_key(
    db: DBSession,
    key_id: str,
    user_id: str | None = None,
) -> bool:
    """Deactivate an API key."""
    api_key = await get_api_key_by_id(db, key_id, user_id)
    if not api_key:
        return False

    api_key.is_active = False  # type: ignore
    await db.commit()
    return True


async def rotate_api_key(
    db: DBSession,
    key_id: str,
    user_id: str | None = None,
) -> tuple[APIKey | None, str | None]:
    """Rotate an API key (deactivate old, create new)."""
    old_key = await get_api_key_by_id(db, key_id, user_id)
    if not old_key:
        return None, None

    # Deactivate the old key
    old_key.is_active = False  # type: ignore

    # Create a new key with the same properties
    new_raw_key = generate_api_key()
    new_key_hash = hash_api_key(new_raw_key)

    new_api_key = APIKey(
        user_id=old_key.user_id,
        key_hash=new_key_hash,
        label=old_key.label,
        scopes=old_key.scopes,
        expires_at=old_key.expires_at,
    )

    db.add(new_api_key)
    await db.commit()

    return new_api_key, new_raw_key


async def get_all_api_keys(
    db: DBSession,
    skip: int = 0,
    limit: int = 100,
) -> list[APIKey]:
    """Get all API keys (admin function)."""
    result = await db.execute(
        select(APIKey)
        .filter(APIKey.is_deleted.is_(False))
        .order_by(APIKey.created_at.desc())
        .offset(skip)
        .limit(limit),
    )

    return list(result.scalars().all())


async def count_all_api_keys(db: DBSession) -> int:
    """Count all API keys (admin function)."""
    result = await db.execute(
        select(APIKey).filter(APIKey.is_deleted.is_(False)),
    )
    return len(result.scalars().all())
