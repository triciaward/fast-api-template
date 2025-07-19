from typing import Optional, Union

from sqlalchemy import select
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


# Sync versions for TestClient compatibility
def get_user_by_email_sync(db: Session, email: str) -> Optional[User]:
    result = db.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none()


def get_user_by_username_sync(db: Session, username: str) -> Optional[User]:
    result = db.execute(select(User).filter(User.username == username))
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
