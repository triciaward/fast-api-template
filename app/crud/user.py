from datetime import datetime
from typing import Optional, Union

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.models import User
from app.schemas.user import UserCreate

# Type alias for both sync and async sessions
DBSession = Union[AsyncSession, Session]


async def get_user_by_email(db: DBSession, email: str) -> Optional[User]:
    if isinstance(db, AsyncSession):
        result = await db.execute(select(User).filter(User.email == email))
    else:
        result = db.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_username(db: DBSession, username: str) -> Optional[User]:
    if isinstance(db, AsyncSession):
        result = await db.execute(select(User).filter(User.username == username))
    else:
        result = db.execute(select(User).filter(User.username == username))
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


async def authenticate_user(db: DBSession, email: str, password: str) -> Optional[User]:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, str(user.hashed_password)):
        return None
    return user


# OAuth CRUD operations
async def get_user_by_oauth_id(
    db: DBSession, oauth_provider: str, oauth_id: str
) -> Optional[User]:
    if isinstance(db, AsyncSession):
        result = await db.execute(
            select(User).filter(
                User.oauth_provider == oauth_provider, User.oauth_id == oauth_id
            )
        )
    else:
        result = db.execute(
            select(User).filter(
                User.oauth_provider == oauth_provider, User.oauth_id == oauth_id
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
    name: Optional[str] = None,
) -> User:
    db_user = User(
        email=email,
        username=username,
        hashed_password=None,  # OAuth users don't have passwords
        is_superuser=False,
        is_verified=True,  # OAuth users are pre-verified
        oauth_provider=oauth_provider,
        oauth_id=oauth_id,
        oauth_email=oauth_email,
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


# Email verification CRUD operations
async def get_user_by_verification_token(db: DBSession, token: str) -> Optional[User]:
    if isinstance(db, AsyncSession):
        result = await db.execute(select(User).filter(User.verification_token == token))
    else:
        result = db.execute(select(User).filter(User.verification_token == token))
    return result.scalar_one_or_none()


async def update_verification_token(
    db: DBSession, user_id: str, token: str, expires: datetime
) -> bool:
    if isinstance(db, AsyncSession):
        result = await db.execute(select(User).filter(User.id == user_id))
    else:
        result = db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return False

    user.verification_token = token  # type: ignore
    user.verification_token_expires = expires  # type: ignore

    if isinstance(db, AsyncSession):
        await db.commit()
    else:
        db.commit()

    return True


async def verify_user(db: DBSession, user_id: str) -> bool:
    if isinstance(db, AsyncSession):
        result = await db.execute(select(User).filter(User.id == user_id))
    else:
        result = db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return False

    user.is_verified = True  # type: ignore
    user.verification_token = None  # type: ignore
    user.verification_token_expires = None  # type: ignore

    if isinstance(db, AsyncSession):
        await db.commit()
    else:
        db.commit()

    return True


# Password reset CRUD operations
async def get_user_by_password_reset_token(db: DBSession, token: str) -> Optional[User]:
    if isinstance(db, AsyncSession):
        result = await db.execute(
            select(User).filter(User.password_reset_token == token)
        )
    else:
        result = db.execute(select(User).filter(User.password_reset_token == token))
    return result.scalar_one_or_none()


async def update_password_reset_token(
    db: DBSession, user_id: str, token: str, expires: datetime
) -> bool:
    if isinstance(db, AsyncSession):
        result = await db.execute(select(User).filter(User.id == user_id))
    else:
        result = db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return False

    user.password_reset_token = token  # type: ignore
    user.password_reset_token_expires = expires  # type: ignore

    if isinstance(db, AsyncSession):
        await db.commit()
    else:
        db.commit()

    return True


async def reset_user_password(db: DBSession, user_id: str, new_password: str) -> bool:
    if isinstance(db, AsyncSession):
        result = await db.execute(select(User).filter(User.id == user_id))
    else:
        result = db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return False

    user.hashed_password = get_password_hash(new_password)  # type: ignore
    user.password_reset_token = None  # type: ignore
    user.password_reset_token_expires = None  # type: ignore

    if isinstance(db, AsyncSession):
        await db.commit()
    else:
        db.commit()

    return True


# Password change CRUD operations
async def update_user_password(db: DBSession, user_id: str, new_password: str) -> bool:
    """Update user password and invalidate any reset tokens."""
    if isinstance(db, AsyncSession):
        result = await db.execute(select(User).filter(User.id == user_id))
    else:
        result = db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return False

    user.hashed_password = get_password_hash(new_password)  # type: ignore
    # Invalidate any existing reset tokens
    user.password_reset_token = None  # type: ignore
    user.password_reset_token_expires = None  # type: ignore

    if isinstance(db, AsyncSession):
        await db.commit()
    else:
        db.commit()

    return True


# Sync versions for TestClient compatibility
def get_user_by_email_sync(db: Session, email: str) -> Optional[User]:
    result = db.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none()


def get_user_by_username_sync(db: Session, username: str) -> Optional[User]:
    result = db.execute(select(User).filter(User.username == username))
    return result.scalar_one_or_none()


def get_user_by_id_sync(db: Session, user_id: str) -> Optional[User]:
    result = db.execute(select(User).filter(User.id == user_id))
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


def authenticate_user_sync(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email_sync(db, email)
    if not user:
        return None
    if not verify_password(password, str(user.hashed_password)):
        return None
    return user


# Sync OAuth operations
def get_user_by_oauth_id_sync(
    db: Session, oauth_provider: str, oauth_id: str
) -> Optional[User]:
    result = db.execute(
        select(User).filter(
            User.oauth_provider == oauth_provider, User.oauth_id == oauth_id
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
    name: Optional[str] = None,
) -> User:
    db_user = User(
        email=email,
        username=username,
        hashed_password=None,  # OAuth users don't have passwords
        is_superuser=False,
        is_verified=True,  # OAuth users are pre-verified
        oauth_provider=oauth_provider,
        oauth_id=oauth_id,
        oauth_email=oauth_email,
    )
    db.add(db_user)
    db.commit()
    try:
        db.refresh(db_user)
    except Exception:
        pass
    return db_user


# Sync email verification operations
def get_user_by_verification_token_sync(db: Session, token: str) -> Optional[User]:
    result = db.execute(select(User).filter(User.verification_token == token))
    return result.scalar_one_or_none()


def update_verification_token_sync(
    db: Session, user_id: str, token: str, expires: datetime
) -> bool:
    result = db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return False

    user.verification_token = token  # type: ignore
    user.verification_token_expires = expires  # type: ignore
    db.commit()

    return True


def verify_user_sync(db: Session, user_id: str) -> bool:
    result = db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return False

    user.is_verified = True  # type: ignore
    user.verification_token = None  # type: ignore
    user.verification_token_expires = None  # type: ignore

    db.commit()

    return True


# Sync password reset operations
def get_user_by_password_reset_token_sync(db: Session, token: str) -> Optional[User]:
    result = db.execute(select(User).filter(User.password_reset_token == token))
    return result.scalar_one_or_none()


def update_password_reset_token_sync(
    db: Session, user_id: str, token: str, expires: datetime
) -> bool:
    result = db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return False

    user.password_reset_token = token  # type: ignore
    user.password_reset_token_expires = expires  # type: ignore

    db.commit()

    return True


def reset_user_password_sync(db: Session, user_id: str, new_password: str) -> bool:
    result = db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return False

    user.hashed_password = get_password_hash(new_password)  # type: ignore
    user.password_reset_token = None  # type: ignore
    user.password_reset_token_expires = None  # type: ignore

    db.commit()

    return True


def update_user_password_sync(db: Session, user_id: str, new_password: str) -> bool:
    """Update user password and invalidate any reset tokens (sync version)."""
    result = db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return False

    user.hashed_password = get_password_hash(new_password)  # type: ignore
    # Invalidate any existing reset tokens
    user.password_reset_token = None  # type: ignore
    user.password_reset_token_expires = None  # type: ignore

    db.commit()
    return True


# Async versions for backward compatibility
async def get_user_by_email_async(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_username_async(db: AsyncSession, username: str) -> Optional[User]:
    result = await db.execute(select(User).filter(User.username == username))
    return result.scalar_one_or_none()


async def create_user_async(db: AsyncSession, user: UserCreate) -> User:
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


async def authenticate_user_async(
    db: AsyncSession, email: str, password: str
) -> Optional[User]:
    user = await get_user_by_email_async(db, email)
    if not user:
        return None
    if not verify_password(password, str(user.hashed_password)):
        return None
    return user


# Account deletion CRUD operations (GDPR compliance)
async def get_user_by_deletion_token(db: DBSession, token: str) -> Optional[User]:
    if isinstance(db, AsyncSession):
        result = await db.execute(select(User).filter(User.deletion_token == token))
    else:
        result = db.execute(select(User).filter(User.deletion_token == token))
    return result.scalar_one_or_none()


async def update_deletion_token(
    db: DBSession, user_id: str, token: str, expires: datetime
) -> bool:
    if isinstance(db, AsyncSession):
        result = await db.execute(select(User).filter(User.id == user_id))
    else:
        result = db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return False

    user.deletion_token = token  # type: ignore
    user.deletion_token_expires = expires  # type: ignore

    if isinstance(db, AsyncSession):
        await db.commit()
    else:
        db.commit()

    return True


async def request_account_deletion(db: DBSession, user_id: str) -> bool:
    if isinstance(db, AsyncSession):
        result = await db.execute(select(User).filter(User.id == user_id))
    else:
        result = db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return False

    user.deletion_requested_at = datetime.utcnow()  # type: ignore

    if isinstance(db, AsyncSession):
        await db.commit()
    else:
        db.commit()

    return True


async def confirm_account_deletion(
    db: DBSession, user_id: str, deletion_scheduled_for: datetime
) -> bool:
    if isinstance(db, AsyncSession):
        result = await db.execute(select(User).filter(User.id == user_id))
    else:
        result = db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return False

    user.deletion_confirmed_at = datetime.utcnow()  # type: ignore
    user.deletion_scheduled_for = deletion_scheduled_for  # type: ignore
    user.deletion_token = None  # type: ignore
    user.deletion_token_expires = None  # type: ignore

    if isinstance(db, AsyncSession):
        await db.commit()
    else:
        db.commit()

    return True


async def cancel_account_deletion(db: DBSession, user_id: str) -> bool:
    if isinstance(db, AsyncSession):
        result = await db.execute(select(User).filter(User.id == user_id))
    else:
        result = db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return False

    user.deletion_requested_at = None  # type: ignore
    user.deletion_confirmed_at = None  # type: ignore
    user.deletion_scheduled_for = None  # type: ignore
    user.deletion_token = None  # type: ignore
    user.deletion_token_expires = None  # type: ignore

    if isinstance(db, AsyncSession):
        await db.commit()
    else:
        db.commit()

    return True


async def permanently_delete_user(db: DBSession, user_id: str) -> bool:
    if isinstance(db, AsyncSession):
        result = await db.execute(select(User).filter(User.id == user_id))
    else:
        result = db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return False

    # Mark as deleted (soft delete for audit purposes)
    user.is_deleted = True  # type: ignore

    if isinstance(db, AsyncSession):
        await db.commit()
    else:
        db.commit()

    return True


# Sync versions for account deletion operations
def get_user_by_deletion_token_sync(db: Session, token: str) -> Optional[User]:
    result = db.execute(select(User).filter(User.deletion_token == token))
    return result.scalar_one_or_none()


def update_deletion_token_sync(
    db: Session, user_id: str, token: str, expires: datetime
) -> bool:
    result = db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return False

    user.deletion_token = token  # type: ignore
    user.deletion_token_expires = expires  # type: ignore

    db.commit()

    return True


def request_account_deletion_sync(db: Session, user_id: str) -> bool:
    result = db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return False

    user.deletion_requested_at = datetime.utcnow()  # type: ignore

    db.commit()

    return True


def confirm_account_deletion_sync(
    db: Session, user_id: str, deletion_scheduled_for: datetime
) -> bool:
    result = db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return False

    user.deletion_confirmed_at = datetime.utcnow()  # type: ignore
    user.deletion_scheduled_for = deletion_scheduled_for  # type: ignore
    user.deletion_token = None  # type: ignore
    user.deletion_token_expires = None  # type: ignore

    db.commit()

    return True


def cancel_account_deletion_sync(db: Session, user_id: str) -> bool:
    result = db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return False

    user.deletion_requested_at = None  # type: ignore
    user.deletion_confirmed_at = None  # type: ignore
    user.deletion_scheduled_for = None  # type: ignore
    user.deletion_token = None  # type: ignore
    user.deletion_token_expires = None  # type: ignore

    db.commit()

    return True


def permanently_delete_user_sync(db: Session, user_id: str) -> bool:
    result = db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return False

    # Mark as deleted (soft delete for audit purposes)
    user.is_deleted = True  # type: ignore

    db.commit()

    return True


# User listing operations
async def get_users(
    db: DBSession,
    skip: int = 0,
    limit: int = 100,
    is_verified: Optional[bool] = None,
    oauth_provider: Optional[str] = None,
    search_query: Optional[str] = None,
    is_superuser: Optional[bool] = None,
    is_deleted: Optional[bool] = None,
    date_created_after: Optional[datetime] = None,
    date_created_before: Optional[datetime] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
) -> list[User]:
    """
    Get users with advanced filtering, search, and pagination.

    Args:
        db: Database session
        skip: Number of users to skip
        limit: Maximum number of users to return
        is_verified: Filter by verification status
        oauth_provider: Filter by OAuth provider
        search_query: Text to search in username and email fields
        is_superuser: Filter by superuser status
        is_deleted: Filter by deletion status
        date_created_after: Filter users created after this date
        date_created_before: Filter users created before this date
        sort_by: Field to sort by
        sort_order: Sort order (asc or desc)

    Returns:
        List[User]: List of users matching criteria
    """
    from app.utils.search_filter import SearchFilterBuilder, create_user_search_filters

    # Create search configuration
    search_config = create_user_search_filters(
        search_query=search_query,
        is_verified=is_verified,
        oauth_provider=oauth_provider,
        is_superuser=is_superuser,
        is_deleted=is_deleted,
        date_created_after=date_created_after,
        date_created_before=date_created_before,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    # Build query with search and filters
    builder = SearchFilterBuilder(User)
    query = builder.build_query(search_config)

    # Apply pagination
    query = query.offset(skip).limit(limit)

    if isinstance(db, AsyncSession):
        result = await db.execute(query)
    else:
        result = db.execute(query)

    return list(result.scalars().all())


async def count_users(
    db: DBSession,
    is_verified: Optional[bool] = None,
    oauth_provider: Optional[str] = None,
    search_query: Optional[str] = None,
    is_superuser: Optional[bool] = None,
    is_deleted: Optional[bool] = None,
    date_created_after: Optional[datetime] = None,
    date_created_before: Optional[datetime] = None,
) -> int:
    """
    Count users with advanced filtering.

    Args:
        db: Database session
        is_verified: Filter by verification status
        oauth_provider: Filter by OAuth provider
        search_query: Text to search in username and email fields
        is_superuser: Filter by superuser status
        is_deleted: Filter by deletion status
        date_created_after: Filter users created after this date
        date_created_before: Filter users created before this date

    Returns:
        int: Number of users matching criteria
    """
    from app.utils.search_filter import SearchFilterBuilder, create_user_search_filters

    # Create search configuration (without sorting for count)
    search_config = create_user_search_filters(
        search_query=search_query,
        is_verified=is_verified,
        oauth_provider=oauth_provider,
        is_superuser=is_superuser,
        is_deleted=is_deleted,
        date_created_after=date_created_after,
        date_created_before=date_created_before,
        sort_by=None,  # No sorting needed for count
        sort_order="asc",
    )

    # Build query with search and filters
    builder = SearchFilterBuilder(User)
    query = builder.build_query(search_config)

    # Convert to count query
    count_query = select(func.count()).select_from(query.subquery())

    if isinstance(db, AsyncSession):
        result = await db.execute(count_query)
    else:
        result = db.execute(count_query)

    return result.scalar() or 0


def get_users_sync(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    is_verified: Optional[bool] = None,
    oauth_provider: Optional[str] = None,
    search_query: Optional[str] = None,
    is_superuser: Optional[bool] = None,
    is_deleted: Optional[bool] = None,
    date_created_after: Optional[datetime] = None,
    date_created_before: Optional[datetime] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
) -> list[User]:
    """
    Get users with advanced filtering, search, and pagination (sync version).

    Args:
        db: Database session
        skip: Number of users to skip
        limit: Maximum number of users to return
        is_verified: Filter by verification status
        oauth_provider: Filter by OAuth provider
        search_query: Text to search in username and email fields
        is_superuser: Filter by superuser status
        is_deleted: Filter by deletion status
        date_created_after: Filter users created after this date
        date_created_before: Filter users created before this date
        sort_by: Field to sort by
        sort_order: Sort order (asc or desc)

    Returns:
        List[User]: List of users matching criteria
    """
    from app.utils.search_filter import SearchFilterBuilder, create_user_search_filters

    # Create search configuration
    search_config = create_user_search_filters(
        search_query=search_query,
        is_verified=is_verified,
        oauth_provider=oauth_provider,
        is_superuser=is_superuser,
        is_deleted=is_deleted,
        date_created_after=date_created_after,
        date_created_before=date_created_before,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    # Build query with search and filters
    builder = SearchFilterBuilder(User)
    query = builder.build_query(search_config)

    # Apply pagination
    query = query.offset(skip).limit(limit)

    result = db.execute(query)
    return list(result.scalars().all())


def count_users_sync(
    db: Session,
    is_verified: Optional[bool] = None,
    oauth_provider: Optional[str] = None,
    search_query: Optional[str] = None,
    is_superuser: Optional[bool] = None,
    is_deleted: Optional[bool] = None,
    date_created_after: Optional[datetime] = None,
    date_created_before: Optional[datetime] = None,
) -> int:
    """
    Count users with advanced filtering (sync version).

    Args:
        db: Database session
        is_verified: Filter by verification status
        oauth_provider: Filter by OAuth provider
        search_query: Text to search in username and email fields
        is_superuser: Filter by superuser status
        is_deleted: Filter by deletion status
        date_created_after: Filter users created after this date
        date_created_before: Filter users created before this date

    Returns:
        int: Number of users matching criteria
    """
    from app.utils.search_filter import SearchFilterBuilder, create_user_search_filters

    # Create search configuration (without sorting for count)
    search_config = create_user_search_filters(
        search_query=search_query,
        is_verified=is_verified,
        oauth_provider=oauth_provider,
        is_superuser=is_superuser,
        is_deleted=is_deleted,
        date_created_after=date_created_after,
        date_created_before=date_created_before,
        sort_by=None,  # No sorting needed for count
        sort_order="asc",
    )

    # Build query with search and filters
    builder = SearchFilterBuilder(User)
    query = builder.build_query(search_config)

    # Convert to count query
    count_query = select(func.count()).select_from(query.subquery())

    result = db.execute(count_query)
    return result.scalar() or 0
