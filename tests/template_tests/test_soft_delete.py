import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.crud import user as crud_user
from app.models import User
from app.schemas.user import UserCreate


@pytest.fixture
def test_user_data() -> dict:
    """Test user data."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPassword123!",
        "is_superuser": False,
    }


@pytest.fixture
def test_user_data_2() -> dict:
    """Second test user data."""
    return {
        "email": "test2@example.com",
        "username": "testuser2",
        "password": "TestPassword123!",
        "is_superuser": False,
    }


@pytest.fixture
def admin_user_data() -> dict:
    """Admin user data."""
    return {
        "email": "admin@example.com",
        "username": "admin",
        "password": "AdminPassword123!",
        "is_superuser": True,
    }


class TestSoftDeleteMixin:
    """Test the SoftDeleteMixin functionality."""

    def test_soft_delete_method(self, sync_db_session: Session, test_user_data: dict):
        """Test that the soft_delete method works correctly."""
        # Create a user
        user_create = UserCreate(**test_user_data)
        user = crud_user.create_user_sync(sync_db_session, user_create)

        # Verify user is not deleted initially
        assert user.is_deleted is False
        assert user.deleted_at is None
        assert user.deleted_by is None
        assert user.deletion_reason is None

        # Soft delete the user
        deleted_by = uuid.uuid4()
        reason = "Test deletion"
        user.soft_delete(deleted_by=deleted_by, reason=reason)

        # Verify soft delete fields are set
        assert user.is_deleted is True
        assert user.deleted_at is not None
        assert user.deleted_by == deleted_by
        assert user.deletion_reason == reason

        # Verify deleted_at is recent
        assert datetime.utcnow() - user.deleted_at < timedelta(seconds=5)

    def test_restore_method(self, sync_db_session: Session, test_user_data: dict):
        """Test that the restore method works correctly."""
        # Create a user
        user_create = UserCreate(**test_user_data)
        user = crud_user.create_user_sync(sync_db_session, user_create)

        # Soft delete the user
        user.soft_delete(deleted_by=uuid.uuid4(), reason="Test deletion")

        # Verify user is deleted
        assert user.is_deleted is True
        assert user.deleted_at is not None

        # Restore the user
        user.restore()

        # Verify user is restored
        assert user.is_deleted is False
        assert user.deleted_at is None
        assert user.deleted_by is None
        assert user.deletion_reason is None

    def test_get_active_query(self, sync_db_session: Session, test_user_data: dict):
        """Test that get_active_query excludes deleted records."""
        # Create a user
        user_create = UserCreate(**test_user_data)
        user = crud_user.create_user_sync(sync_db_session, user_create)

        # Verify user appears in active query
        active_users = sync_db_session.execute(User.get_active_query()).scalars().all()
        assert user in active_users

        # Soft delete the user
        user.soft_delete()
        sync_db_session.commit()  # Commit the changes to the database

        # Verify user no longer appears in active query
        active_users = sync_db_session.execute(User.get_active_query()).scalars().all()
        assert user not in active_users

    def test_get_deleted_query(self, sync_db_session: Session, test_user_data: dict):
        """Test that get_deleted_query includes only deleted records."""
        # Create a user
        user_create = UserCreate(**test_user_data)
        user = crud_user.create_user_sync(sync_db_session, user_create)

        # Verify user doesn't appear in deleted query
        deleted_users = (
            sync_db_session.execute(User.get_deleted_query()).scalars().all()
        )
        assert user not in deleted_users

        # Soft delete the user
        user.soft_delete()
        sync_db_session.commit()  # Commit the changes to the database

        # Verify user appears in deleted query
        deleted_users = (
            sync_db_session.execute(User.get_deleted_query()).scalars().all()
        )
        assert user in deleted_users

    def test_get_all_query(self, sync_db_session: Session, test_user_data: dict):
        """Test that get_all_query includes all records."""
        # Create a user
        user_create = UserCreate(**test_user_data)
        user = crud_user.create_user_sync(sync_db_session, user_create)

        # Verify user appears in all query
        all_users = sync_db_session.execute(User.get_all_query()).scalars().all()
        assert user in all_users

        # Soft delete the user
        user.soft_delete()
        sync_db_session.commit()  # Commit the changes to the database

        # Verify user still appears in all query
        all_users = sync_db_session.execute(User.get_all_query()).scalars().all()
        assert user in all_users


@pytest.mark.skip(
    reason="Requires complex soft delete functionality - not implemented yet"
)
class TestSoftDeleteCRUD:
    """Test the soft delete CRUD operations."""

    def test_soft_delete_user(self, sync_db_session: Session, test_user_data: dict):
        """Test soft deleting a user via CRUD."""
        # Create a user
        user_create = UserCreate(**test_user_data)
        user = crud_user.create_user_sync(sync_db_session, user_create)

        # Soft delete the user
        success = crud_user.soft_delete_user_sync(sync_db_session, str(user.id))

        assert success is True

        # Verify user is soft deleted
        updated_user = crud_user.get_user_by_id_any_status_sync(
            sync_db_session, str(user.id)
        )
        assert updated_user is not None
        assert updated_user.is_deleted is True
        assert updated_user.deleted_at is not None

    def test_restore_user(self, sync_db_session: Session, test_user_data: dict):
        """Test restoring a user via CRUD."""
        # Create a user
        user_create = UserCreate(**test_user_data)
        user = crud_user.create_user_sync(sync_db_session, user_create)

        # Soft delete the user
        crud_user.soft_delete_user_sync(sync_db_session, str(user.id))

        # Restore the user
        success = crud_user.restore_user_sync(sync_db_session, str(user.id))

        assert success is True

        # Verify user is restored
        updated_user = crud_user.get_user_by_id_sync(sync_db_session, str(user.id))
        assert updated_user is not None
        assert updated_user.is_deleted is False
        assert updated_user.deleted_at is None

    def test_get_deleted_users(
        self, sync_db_session: Session, test_user_data: dict, test_user_data_2: dict
    ):
        """Test getting deleted users."""
        # Create two users
        user1 = crud_user.create_user_sync(
            sync_db_session, UserCreate(**test_user_data)
        )
        crud_user.create_user_sync(sync_db_session, UserCreate(**test_user_data_2))

        # Soft delete one user
        crud_user.soft_delete_user_sync(sync_db_session, str(user1.id))

        # Get deleted users
        deleted_users = crud_user.get_deleted_users_sync(sync_db_session)

        assert len(deleted_users) == 1
        assert deleted_users[0].id == user1.id
        assert deleted_users[0].is_deleted is True

    def test_count_deleted_users(
        self, sync_db_session: Session, test_user_data: dict, test_user_data_2: dict
    ):
        """Test counting deleted users."""
        # Create two users
        user1 = crud_user.create_user_sync(
            sync_db_session, UserCreate(**test_user_data)
        )
        crud_user.create_user_sync(sync_db_session, UserCreate(**test_user_data_2))

        # Initially no deleted users
        count = crud_user.count_deleted_users_sync(sync_db_session)
        assert count == 0

        # Soft delete one user
        crud_user.soft_delete_user_sync(sync_db_session, str(user1.id))

        # Now one deleted user
        count = crud_user.count_deleted_users_sync(sync_db_session)
        assert count == 1

    def test_permanently_delete_user(
        self, sync_db_session: Session, test_user_data: dict
    ):
        """Test permanently deleting a user."""
        # Create a user
        user_create = UserCreate(**test_user_data)
        user = crud_user.create_user_sync(sync_db_session, user_create)
        user_id = str(user.id)

        # Permanently delete the user
        success = crud_user.permanently_delete_user_sync(sync_db_session, user_id)

        assert success is True

        # Verify user is completely removed
        deleted_user = crud_user.get_user_by_id_sync(sync_db_session, user_id)
        assert deleted_user is None

    def test_soft_delete_nonexistent_user(self, sync_db_session: Session):
        """Test soft deleting a user that doesn't exist."""
        nonexistent_id = str(uuid.uuid4())
        success = crud_user.soft_delete_user_sync(sync_db_session, nonexistent_id)
        assert success is False

    def test_restore_nonexistent_user(self, sync_db_session: Session):
        """Test restoring a user that doesn't exist."""
        nonexistent_id = str(uuid.uuid4())
        success = crud_user.restore_user_sync(sync_db_session, nonexistent_id)
        assert success is False

    def test_restore_already_active_user(
        self, sync_db_session: Session, test_user_data: dict
    ):
        """Test restoring a user that is already active."""
        # Create a user (already active)
        user_create = UserCreate(**test_user_data)
        user = crud_user.create_user_sync(sync_db_session, user_create)

        # Try to restore (should fail)
        success = crud_user.restore_user_sync(sync_db_session, str(user.id))
        assert success is False

    def test_soft_delete_already_deleted_user(
        self, sync_db_session: Session, test_user_data: dict
    ):
        """Test soft deleting a user that is already deleted."""
        # Create a user
        user_create = UserCreate(**test_user_data)
        user = crud_user.create_user_sync(sync_db_session, user_create)

        # Soft delete the user
        crud_user.soft_delete_user_sync(sync_db_session, str(user.id))

        # Try to soft delete again (should fail)
        success = crud_user.soft_delete_user_sync(sync_db_session, str(user.id))
        assert success is False


@pytest.mark.skip(
    reason="Requires complex soft delete functionality - not implemented yet"
)
class TestSoftDeleteIntegration:
    """Test soft delete integration with existing functionality."""

    def test_deleted_users_not_in_normal_queries(
        self, sync_db_session: Session, test_user_data: dict
    ):
        """Test that deleted users don't appear in normal queries."""
        # Create a user
        user_create = UserCreate(**test_user_data)
        user = crud_user.create_user_sync(sync_db_session, user_create)

        # Verify user appears in normal queries
        users = crud_user.get_users_sync(sync_db_session)
        assert user in users

        # Soft delete the user
        crud_user.soft_delete_user_sync(sync_db_session, str(user.id))

        # Verify user no longer appears in normal queries
        users = crud_user.get_users_sync(sync_db_session)
        assert user not in users

    def test_deleted_users_not_authenticatable(
        self, sync_db_session: Session, test_user_data: dict
    ):
        """Test that deleted users cannot authenticate."""
        # Create a user
        user_create = UserCreate(**test_user_data)
        user = crud_user.create_user_sync(sync_db_session, user_create)

        # Verify user can authenticate
        auth_user = crud_user.authenticate_user_sync(
            sync_db_session, test_user_data["email"], test_user_data["password"]
        )
        assert auth_user is not None
        assert auth_user.id == user.id

        # Soft delete the user
        crud_user.soft_delete_user_sync(sync_db_session, str(user.id))

        # Verify user cannot authenticate
        auth_user = crud_user.authenticate_user_sync(
            sync_db_session, test_user_data["email"], test_user_data["password"]
        )
        assert auth_user is None

    def test_deleted_users_not_findable_by_email(
        self, sync_db_session: Session, test_user_data: dict
    ):
        """Test that deleted users cannot be found by email."""
        # Create a user
        user_create = UserCreate(**test_user_data)
        user = crud_user.create_user_sync(sync_db_session, user_create)

        # Verify user can be found by email
        found_user = crud_user.get_user_by_email_sync(
            sync_db_session, test_user_data["email"]
        )
        assert found_user is not None
        assert found_user.id == user.id

        # Soft delete the user
        crud_user.soft_delete_user_sync(sync_db_session, str(user.id))

        # Verify user cannot be found by email
        found_user = crud_user.get_user_by_email_sync(
            sync_db_session, test_user_data["email"]
        )
        assert found_user is None

    def test_deleted_users_not_findable_by_username(
        self, sync_db_session: Session, test_user_data: dict
    ):
        """Test that deleted users cannot be found by username."""
        # Create a user
        user_create = UserCreate(**test_user_data)
        user = crud_user.create_user_sync(sync_db_session, user_create)

        # Verify user can be found by username
        found_user = crud_user.get_user_by_username_sync(
            sync_db_session, test_user_data["username"]
        )
        assert found_user is not None
        assert found_user.id == user.id

        # Soft delete the user
        crud_user.soft_delete_user_sync(sync_db_session, str(user.id))

        # Verify user cannot be found by username
        found_user = crud_user.get_user_by_username_sync(
            sync_db_session, test_user_data["username"]
        )
        assert found_user is None
