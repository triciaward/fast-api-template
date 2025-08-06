"""
Admin-specific CRUD operations.

This module provides admin-only CRUD operations for managing users and other resources.
All operations require superuser privileges.
"""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.admin import BaseAdminCRUD, DBSession
from app.core.security import get_password_hash
from app.crud import user as crud_user
from app.models import User
from app.schemas.admin import AdminUserUpdate
from app.schemas.user import UserCreate, UserResponse


class AdminUserCRUD(BaseAdminCRUD[User, UserCreate, AdminUserUpdate, UserResponse]):
    """
    Admin-specific CRUD operations for user management.

    This class provides admin-only operations for managing users, including:
    - Listing all users with filtering and pagination
    - Creating, updating, and deleting users
    - Managing user privileges and status
    - Bulk operations
    """

    def __init__(self):
        """Initialize the AdminUserCRUD with the User model."""
        super().__init__(User)

    async def get_users(
        self,
        db: DBSession,
        skip: int = 0,
        limit: int = 100,
        is_superuser: bool | None = None,
        is_verified: bool | None = None,
        is_deleted: bool | None = None,
        oauth_provider: str | None = None,
    ) -> list[User]:
        """
        Get users with optional filtering.

        Args:
            db: Database session
            skip: Number of users to skip
            limit: Maximum number of users to return
            is_superuser: Filter by superuser status
            is_verified: Filter by verification status
            is_deleted: Filter by deletion status
            oauth_provider: Filter by OAuth provider

        Returns:
            List[User]: List of users matching criteria
        """
        filters: dict[str, Any] = {}
        if is_superuser is not None:
            filters["is_superuser"] = is_superuser
        if is_verified is not None:
            filters["is_verified"] = is_verified
        if is_deleted is not None:
            filters["is_deleted"] = is_deleted
        if oauth_provider is not None:
            filters["oauth_provider"] = oauth_provider

        return await self.get_multi(db, skip=skip, limit=limit, filters=filters)

    async def get_user_by_email(self, db: DBSession, email: str) -> User | None:
        """
        Get user by email address.

        Args:
            db: Database session
            email: User's email address

        Returns:
            Optional[User]: User if found, None otherwise
        """
        if isinstance(db, AsyncSession):
            result = await db.execute(select(User).filter(User.email == email))
        else:
            result = db.execute(select(User).filter(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_username(self, db: DBSession, username: str) -> User | None:
        """
        Get user by username.

        Args:
            db: Database session
            username: User's username

        Returns:
            Optional[User]: User if found, None otherwise
        """
        if isinstance(db, AsyncSession):
            result = await db.execute(select(User).filter(User.username == username))
        else:
            result = db.execute(select(User).filter(User.username == username))
        return result.scalar_one_or_none()

    async def create_user(self, db: DBSession, user_data: UserCreate) -> User:
        """
        Create a new user (admin-only).

        Args:
            db: Database session
            user_data: User creation data

        Returns:
            User: Created user
        """
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            is_superuser=user_data.is_superuser,
            is_verified=False,  # Default to False for new users
        )
        db.add(db_user)

        if isinstance(db, AsyncSession):
            await db.commit()
            await db.refresh(db_user)
        else:
            db.commit()
            db.refresh(db_user)

        return db_user

    async def update_user(
        self,
        db: DBSession,
        user_id: str | UUID,
        user_data: AdminUserUpdate,
    ) -> User | None:
        """
        Update user data (admin-only).

        Args:
            db: Database session
            user_id: User ID
            user_data: User update data

        Returns:
            Optional[User]: Updated user if found, None otherwise
        """
        user = await self.get(db, user_id)
        if not user:
            return None

        update_data = user_data.model_dump(exclude_unset=True)

        # Handle password hashing if password is being updated
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(
                update_data.pop("password"),
            )

        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)

        db.add(user)

        if isinstance(db, AsyncSession):
            await db.commit()
            await db.refresh(user)
        else:
            db.commit()
            db.refresh(user)

        return user

    async def delete_user(self, db: DBSession, user_id: str | UUID) -> bool:
        """
        Delete a user (admin-only).

        Args:
            db: Database session
            user_id: User ID

        Returns:
            bool: True if deleted, False if not found
        """
        return await self.delete(db, user_id)

    async def toggle_superuser_status(
        self,
        db: DBSession,
        user_id: str | UUID,
    ) -> User | None:
        """
        Toggle superuser status for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Optional[User]: Updated user if found, None otherwise
        """
        user = await self.get(db, user_id)
        if not user:
            return None

        user.is_superuser = not user.is_superuser  # type: ignore
        db.add(user)

        if isinstance(db, AsyncSession):
            await db.commit()
            await db.refresh(user)
        else:
            db.commit()
            db.refresh(user)

        return user

    async def toggle_verification_status(
        self,
        db: DBSession,
        user_id: str | UUID,
    ) -> User | None:
        """
        Toggle verification status for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Optional[User]: Updated user if found, None otherwise
        """
        user = await self.get(db, user_id)
        if not user:
            return None

        user.is_verified = not user.is_verified  # type: ignore
        db.add(user)

        if isinstance(db, AsyncSession):
            await db.commit()
            await db.refresh(user)
        else:
            db.commit()
            db.refresh(user)

        return user

    async def force_delete_user(self, db: DBSession, user_id: str | UUID) -> bool:
        """
        Force delete a user (bypasses normal deletion flow).

        Args:
            db: Database session
            user_id: User ID

        Returns:
            bool: True if deleted, False if not found
        """
        # Use the soft delete function with admin context
        return await crud_user.soft_delete_user(
            db=db,
            user_id=str(user_id),
        )

    async def get_user_statistics(self, db: DBSession) -> dict:
        """
        Get user statistics for admin dashboard.

        Args:
            db: Database session

        Returns:
            dict: User statistics
        """
        from sqlalchemy import func

        # Total users
        total_query = select(func.count(User.id))
        if isinstance(db, AsyncSession):
            total_result = await db.execute(total_query)
        else:
            total_result = db.execute(total_query)
        total_users = total_result.scalar() or 0

        # Superusers
        superuser_query = select(func.count(User.id)).where(User.is_superuser == True)  # type: ignore # noqa: E712
        if isinstance(db, AsyncSession):
            superuser_result = await db.execute(superuser_query)
        else:
            superuser_result = db.execute(superuser_query)
        superusers = superuser_result.scalar() or 0

        # Verified users
        verified_query = select(func.count(User.id)).where(User.is_verified == True)  # type: ignore # noqa: E712
        if isinstance(db, AsyncSession):
            verified_result = await db.execute(verified_query)
        else:
            verified_result = db.execute(verified_query)
        verified_users = verified_result.scalar() or 0

        # OAuth users
        oauth_query = select(func.count(User.id)).where(User.oauth_provider.isnot(None))
        if isinstance(db, AsyncSession):
            oauth_result = await db.execute(oauth_query)
        else:
            oauth_result = db.execute(oauth_query)
        oauth_users = oauth_result.scalar() or 0

        # Deleted users
        deleted_query = select(func.count(User.id)).where(User.is_deleted == True)  # type: ignore # noqa: E712
        if isinstance(db, AsyncSession):
            deleted_result = await db.execute(deleted_query)
        else:
            deleted_result = db.execute(deleted_query)
        deleted_users = deleted_result.scalar() or 0

        return {
            "total_users": total_users,
            "superusers": superusers,
            "verified_users": verified_users,
            "oauth_users": oauth_users,
            "deleted_users": deleted_users,
            "regular_users": total_users - superusers,
            "unverified_users": total_users - verified_users,
        }

    async def get_deleted_users(
        self,
        db: DBSession,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """
        Get deleted users with pagination.

        Args:
            db: Database session
            skip: Number of users to skip
            limit: Maximum number of users to return

        Returns:
            List[User]: List of deleted users
        """
        filters = {"is_deleted": True}
        return await self.get_multi(db, skip=skip, limit=limit, filters=filters)

    async def count_deleted_users(self, db: DBSession) -> int:
        """
        Count deleted users.

        Args:
            db: Database session

        Returns:
            int: Number of deleted users
        """
        filters = {"is_deleted": True}
        return await self.count(db, filters=filters)


# Create a singleton instance for easy import
admin_user_crud = AdminUserCRUD()
