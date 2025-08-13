"""
Admin-specific utilities and base classes.

This module provides admin-only utilities, base classes, and dependencies for admin operations.
"""

import logging
from collections.abc import Callable
from typing import Any, Generic, Protocol, TypeAlias, TypeVar
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.database import get_db

# Removed schemas import to avoid circular dependency - using local imports

logger = logging.getLogger(__name__)

# Protocol to ensure models have an id attribute


class HasId(Protocol):
    id: Any


# Type variables for generic CRUD operations
ModelType = TypeVar("ModelType", bound=HasId)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)

# Type alias for database sessions (now async only)
DBSession: TypeAlias = AsyncSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get the current authenticated user.

    This function extracts the user from the JWT token and returns the user data.
    It's used as a dependency for endpoints that require authentication.

    Args:
        token: JWT token from the Authorization header
        db: Database session

    Returns:
        UserResponse: Current user data

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        # Local import to avoid circular dependency
        from app.schemas.auth.user import TokenData

        TokenData(email=None)
    except JWTError as e:
        raise credentials_exception from e

    # Local import to avoid circular dependency
    from app.crud.auth.user import get_user_by_id

    user = await get_user_by_id(db, user_id=str(user_id))
    if user is None:
        raise credentials_exception
    return user


async def require_superuser(
    current_user: Any = Depends(get_current_user),
) -> Any:
    """
    Require superuser privileges.

    This function ensures that the current user has superuser privileges.
    It's used as a dependency for admin-only endpoints.

    Args:
        current_user: Current authenticated user

    Returns:
        UserResponse: Current user data (if superuser)

    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        logger.warning(
            "Non-superuser attempted to access admin endpoint",
            extra={"user_id": str(current_user.id)},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser privileges required",
        )
    return current_user


class BaseAdminCRUD(
    Generic[ModelType, CreateSchemaType, UpdateSchemaType, ResponseSchemaType],
):
    """
    Base class for admin CRUD operations.

    This class provides common CRUD operations that can be used by admin-specific
    CRUD classes. It's designed to work with both sync and async database sessions.

    Generic Types:
        ModelType: SQLAlchemy model class
        CreateSchemaType: Pydantic schema for creation
        UpdateSchemaType: Pydantic schema for updates
        ResponseSchemaType: Pydantic schema for responses
    """

    def __init__(self, model: type[ModelType]):
        """
        Initialize the base admin CRUD.

        Args:
            model: SQLAlchemy model class
        """
        self.model = model

    async def get_multi(
        self,
        db: DBSession,
        skip: int = 0,
        limit: int = 100,
        filters: dict[str, Any] | None = None,
    ) -> list[ModelType]:
        """
        Get multiple records with optional filtering and pagination.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Optional filters to apply

        Returns:
            List[ModelType]: List of records
        """
        query = select(self.model)

        # Apply filters if provided
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)

        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get(self, db: DBSession, record_id: str | UUID) -> ModelType | None:
        """
        Get a single record by ID.

        Args:
            db: Database session
            id: Record ID

        Returns:
            Optional[ModelType]: Record if found, None otherwise
        """
        result = await db.execute(
            select(self.model).filter(self.model.id == record_id),
        )
        return result.scalar_one_or_none()

    async def create(self, db: DBSession, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record.

        Args:
            db: Database session
            obj_in: Data for creating the record

        Returns:
            ModelType: Created record
        """
        obj_data = obj_in.model_dump()
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: DBSession,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict[str, Any],
    ) -> ModelType:
        """
        Update an existing record.

        Args:
            db: Database session
            db_obj: Existing record
            obj_in: Update data

        Returns:
            ModelType: Updated record
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: DBSession, record_id: str | UUID) -> bool:
        """
        Delete a record by ID.

        Args:
            db: Database session
            id: Record ID

        Returns:
            bool: True if deleted, False if not found
        """
        obj = await self.get(db, record_id)
        if not obj:
            return False

        await db.delete(obj)
        await db.commit()
        return True

    async def count(self, db: DBSession, filters: dict[str, Any] | None = None) -> int:
        """
        Count records with optional filtering.

        Args:
            db: Database session
            filters: Optional filters to apply

        Returns:
            int: Number of records
        """
        from sqlalchemy import func

        query = select(func.count(self.model.id))

        # Apply filters if provided
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)

        result = await db.execute(query)
        count_result = result.scalar()
        return count_result if count_result is not None else 0


def admin_only_endpoint(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to mark endpoints as admin-only.

    This decorator can be used to mark endpoints that require superuser privileges.
    It's a convenience decorator that can be used for documentation purposes.

    Args:
        func: Function to decorate

    Returns:
        Callable: Decorated function
    """
    # Add admin-only metadata to the function
    func.__admin_only__ = True  # type: ignore
    return func
