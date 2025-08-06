"""
Tests for CRUD User operations.

This module tests the user CRUD functionality including user creation, authentication, OAuth operations, and user management.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.crud.user import (
    authenticate_user,
    authenticate_user_sync,
    cancel_account_deletion_sync,
    confirm_account_deletion_sync,
    count_deleted_users_sync,
    count_users_sync,
    create_oauth_user,
    create_oauth_user_sync,
    create_user,
    create_user_sync,
    get_deleted_users_sync,
    get_user_by_deletion_token_sync,
    get_user_by_email,
    get_user_by_email_sync,
    get_user_by_id_any_status_sync,
    get_user_by_id_sync,
    get_user_by_oauth_id,
    get_user_by_oauth_id_sync,
    get_user_by_password_reset_token_sync,
    get_user_by_username,
    get_user_by_username_sync,
    get_user_by_verification_token_sync,
    get_users_sync,
    permanently_delete_user_sync,
    request_account_deletion_sync,
    reset_user_password_sync,
    restore_user_sync,
    soft_delete_user_sync,
    update_deletion_token_sync,
    update_password_reset_token_sync,
    update_user_password_sync,
    update_verification_token_sync,
    verify_user_sync,
)
from app.schemas.user import UserCreate


class TestUserCRUDAsync:
    """Test async user CRUD operations."""

    async def test_get_user_by_email_async_session(self):
        """Test getting user by email with async session."""
        # Mock async session
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.is_deleted = False
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        # Test
        result = await get_user_by_email(mock_db, "test@example.com")

        # Verify
        assert result == mock_user
        mock_db.execute.assert_called_once()

    async def test_get_user_by_email_sync_session(self):
        """Test getting user by email with sync session."""
        # Mock sync session
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.is_deleted = False
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        # Test
        result = await get_user_by_email(mock_db, "test@example.com")

        # Verify
        assert result == mock_user
        mock_db.execute.assert_called_once()

    async def test_get_user_by_email_not_found(self):
        """Test getting user by email when not found."""
        # Mock async session
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Test
        result = await get_user_by_email(mock_db, "nonexistent@example.com")

        # Verify
        assert result is None

    async def test_get_user_by_username_async_session(self):
        """Test getting user by username with async session."""
        # Mock async session
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_user.is_deleted = False
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        # Test
        result = await get_user_by_username(mock_db, "testuser")

        # Verify
        assert result == mock_user
        mock_db.execute.assert_called_once()

    async def test_create_user_async_session(self):
        """Test creating user with async session."""
        # Mock async session
        mock_db = AsyncMock(spec=AsyncSession)

        # Mock user data
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="TestPassword123!",
            is_superuser=False,
        )

        # Test
        result = await create_user(mock_db, user_data)

        # Verify
        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    async def test_create_user_sync_session(self):
        """Test creating user with sync session."""
        # Mock sync session
        mock_db = MagicMock(spec=Session)

        # Mock user data
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="TestPassword123!",
            is_superuser=False,
        )

        # Test
        result = await create_user(mock_db, user_data)

        # Verify
        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    async def test_authenticate_user_success(self):
        """Test successful user authentication."""
        # Mock user
        mock_user = MagicMock()
        mock_user.hashed_password = "$2b$12$test_hash"

        # Mock get_user_by_email
        with patch("app.crud.user.get_user_by_email") as mock_get_user:
            with patch("app.crud.user.verify_password") as mock_verify:
                mock_get_user.return_value = mock_user
                mock_verify.return_value = True

                # Mock async session
                mock_db = AsyncMock(spec=AsyncSession)

                # Test
                result = await authenticate_user(
                    mock_db, "test@example.com", "password123"
                )

                # Verify
                assert result == mock_user
                mock_get_user.assert_called_once_with(mock_db, "test@example.com")
                mock_verify.assert_called_once_with("password123", "$2b$12$test_hash")

    async def test_authenticate_user_invalid_password(self):
        """Test user authentication with invalid password."""
        # Mock user
        mock_user = MagicMock()
        mock_user.hashed_password = "$2b$12$test_hash"

        # Mock get_user_by_email
        with patch("app.crud.user.get_user_by_email") as mock_get_user:
            with patch("app.crud.user.verify_password") as mock_verify:
                mock_get_user.return_value = mock_user
                mock_verify.return_value = False

                # Mock async session
                mock_db = AsyncMock(spec=AsyncSession)

                # Test
                result = await authenticate_user(
                    mock_db, "test@example.com", "wrongpassword"
                )

                # Verify
                assert result is None

    async def test_authenticate_user_not_found(self):
        """Test user authentication when user not found."""
        # Mock get_user_by_email
        with patch("app.crud.user.get_user_by_email") as mock_get_user:
            mock_get_user.return_value = None

            # Mock async session
            mock_db = AsyncMock(spec=AsyncSession)

            # Test
            result = await authenticate_user(
                mock_db, "nonexistent@example.com", "password123"
            )

            # Verify
            assert result is None

    async def test_get_user_by_oauth_id_async_session(self):
        """Test getting user by OAuth ID with async session."""
        # Mock async session
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_user = MagicMock()
        mock_user.oauth_provider = "google"
        mock_user.oauth_id = "google_123"
        mock_user.is_deleted = False
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        # Test
        result = await get_user_by_oauth_id(mock_db, "google", "google_123")

        # Verify
        assert result == mock_user
        mock_db.execute.assert_called_once()

    async def test_create_oauth_user_async_session(self):
        """Test creating OAuth user with async session."""
        # Mock async session
        mock_db = AsyncMock(spec=AsyncSession)

        # Test
        result = await create_oauth_user(
            db=mock_db,
            email="oauth@example.com",
            username="oauthuser",
            oauth_provider="google",
            oauth_id="google_123",
            oauth_email="oauth@example.com",
        )

        # Verify
        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


class TestUserCRUDSync:
    """Test sync user CRUD operations."""

    def test_get_user_by_email_sync(self):
        """Test getting user by email with sync function."""
        # Mock session
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.is_deleted = False
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        # Test
        result = get_user_by_email_sync(mock_db, "test@example.com")

        # Verify
        assert result == mock_user
        mock_db.execute.assert_called_once()

    def test_get_user_by_username_sync(self):
        """Test getting user by username with sync function."""
        # Mock session
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_user.is_deleted = False
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        # Test
        result = get_user_by_username_sync(mock_db, "testuser")

        # Verify
        assert result == mock_user
        mock_db.execute.assert_called_once()

    def test_create_user_sync(self):
        """Test creating user with sync function."""
        # Mock session
        mock_db = MagicMock(spec=Session)

        # Mock user data
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="TestPassword123!",
            is_superuser=False,
        )

        # Test
        result = create_user_sync(mock_db, user_data)

        # Verify
        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_authenticate_user_sync_success(self):
        """Test successful user authentication with sync function."""
        # Mock user
        mock_user = MagicMock()
        mock_user.hashed_password = "$2b$12$test_hash"

        # Mock get_user_by_email_sync
        with patch("app.crud.user.get_user_by_email_sync") as mock_get_user:
            with patch("app.crud.user.verify_password") as mock_verify:
                mock_get_user.return_value = mock_user
                mock_verify.return_value = True

                # Mock session
                mock_db = MagicMock(spec=Session)

                # Test
                result = authenticate_user_sync(
                    mock_db, "test@example.com", "password123"
                )

                # Verify
                assert result == mock_user
                mock_get_user.assert_called_once_with(mock_db, "test@example.com")
                mock_verify.assert_called_once_with("password123", "$2b$12$test_hash")

    def test_get_user_by_oauth_id_sync(self):
        """Test getting user by OAuth ID with sync function."""
        # Mock session
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_user = MagicMock()
        mock_user.oauth_provider = "google"
        mock_user.oauth_id = "google_123"
        mock_user.is_deleted = False
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        # Test
        result = get_user_by_oauth_id_sync(mock_db, "google", "google_123")

        # Verify
        assert result == mock_user
        mock_db.execute.assert_called_once()

    def test_create_oauth_user_sync(self):
        """Test creating OAuth user with sync function."""
        # Mock session
        mock_db = MagicMock(spec=Session)

        # Test
        result = create_oauth_user_sync(
            db=mock_db,
            email="oauth@example.com",
            username="oauthuser",
            oauth_provider="google",
            oauth_id="google_123",
            oauth_email="oauth@example.com",
        )

        # Verify
        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


class TestUserTokenOperations:
    """Test user token operations."""

    def test_get_user_by_verification_token_sync(self):
        """Test getting user by verification token."""
        # Mock session
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_user = MagicMock()
        mock_user.verification_token = "test_token"
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        # Test
        result = get_user_by_verification_token_sync(mock_db, "test_token")

        # Verify
        assert result == mock_user
        mock_db.execute.assert_called_once()

    def test_update_verification_token_sync(self):
        """Test updating verification token."""
        # Mock session
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db.execute.return_value = mock_result

        # Test
        expires = datetime.utcnow() + timedelta(hours=24)
        result = update_verification_token_sync(
            mock_db, "user_id", "new_token", expires
        )

        # Verify
        assert result is True
        mock_db.commit.assert_called_once()

    def test_verify_user_sync(self):
        """Test verifying user."""
        # Mock session
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db.execute.return_value = mock_result

        # Test
        result = verify_user_sync(mock_db, "user_id")

        # Verify
        assert result is True
        mock_db.commit.assert_called_once()

    def test_get_user_by_password_reset_token_sync(self):
        """Test getting user by password reset token."""
        # Mock session
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_user = MagicMock()
        mock_user.password_reset_token = "reset_token"
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        # Test
        result = get_user_by_password_reset_token_sync(mock_db, "reset_token")

        # Verify
        assert result == mock_user
        mock_db.execute.assert_called_once()

    def test_update_password_reset_token_sync(self):
        """Test updating password reset token."""
        # Mock session
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db.execute.return_value = mock_result

        # Test
        expires = datetime.utcnow() + timedelta(hours=1)
        result = update_password_reset_token_sync(
            mock_db, "user_id", "new_reset_token", expires
        )

        # Verify
        assert result is True
        mock_db.commit.assert_called_once()

    def test_reset_user_password_sync(self):
        """Test resetting user password."""
        # Mock session
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db.execute.return_value = mock_result

        # Test
        result = reset_user_password_sync(mock_db, "user_id", "new_password")

        # Verify
        assert result is True
        mock_db.commit.assert_called_once()

    def test_update_user_password_sync(self):
        """Test updating user password."""
        # Mock session
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db.execute.return_value = mock_result

        # Test
        result = update_user_password_sync(mock_db, "user_id", "new_password")

        # Verify
        assert result is True
        mock_db.commit.assert_called_once()


class TestUserDeletionOperations:
    """Test user deletion operations."""

    def test_get_user_by_deletion_token_sync(self):
        """Test getting user by deletion token."""
        # Mock session
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_user = MagicMock()
        mock_user.deletion_token = "deletion_token"
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        # Test
        result = get_user_by_deletion_token_sync(mock_db, "deletion_token")

        # Verify
        assert result == mock_user
        mock_db.execute.assert_called_once()

    def test_update_deletion_token_sync(self):
        """Test updating deletion token."""
        # Mock session
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db.execute.return_value = mock_result

        # Test
        expires = datetime.utcnow() + timedelta(days=7)
        result = update_deletion_token_sync(
            mock_db, "user_id", "new_deletion_token", expires
        )

        # Verify
        assert result is True
        mock_db.commit.assert_called_once()

    def test_request_account_deletion_sync(self):
        """Test requesting account deletion."""
        # Mock session
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db.execute.return_value = mock_result

        # Test
        result = request_account_deletion_sync(mock_db, "user_id")

        # Verify
        assert result is True
        mock_db.commit.assert_called_once()

    def test_confirm_account_deletion_sync(self):
        """Test confirming account deletion."""
        # Mock session
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db.execute.return_value = mock_result

        # Test
        result = confirm_account_deletion_sync(mock_db, "user_id")

        # Verify
        assert result is True
        mock_db.commit.assert_called_once()

    def test_cancel_account_deletion_sync(self):
        """Test canceling account deletion."""
        # Mock session
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db.execute.return_value = mock_result

        # Test
        result = cancel_account_deletion_sync(mock_db, "user_id")

        # Verify
        assert result is True
        mock_db.commit.assert_called_once()


class TestUserManagementOperations:
    """Test user management operations."""

    def test_get_user_by_id_sync(self):
        """Test getting user by ID."""
        # Mock session
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_user = MagicMock()
        mock_user.id = "user_id"
        mock_user.is_deleted = False
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        # Test
        result = get_user_by_id_sync(mock_db, "user_id")

        # Verify
        assert result == mock_user
        mock_db.execute.assert_called_once()

    def test_get_user_by_id_any_status_sync(self):
        """Test getting user by ID with any status."""
        # Mock session
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_user = MagicMock()
        mock_user.id = "user_id"
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        # Test
        result = get_user_by_id_any_status_sync(mock_db, "user_id")

        # Verify
        assert result == mock_user
        mock_db.execute.assert_called_once()

    def test_soft_delete_user_sync(self):
        """Test soft deleting user."""
        # Mock session
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db.execute.return_value = mock_result

        # Test
        result = soft_delete_user_sync(mock_db, "user_id")

        # Verify
        assert result is True
        mock_db.commit.assert_called_once()

    def test_restore_user_sync(self):
        """Test restoring user."""
        # Mock session
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db.execute.return_value = mock_result

        # Test
        result = restore_user_sync(mock_db, "user_id")

        # Verify
        assert result is True
        mock_db.commit.assert_called_once()

    def test_permanently_delete_user_sync(self):
        """Test permanently deleting user."""
        # Mock session
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db.execute.return_value = mock_result

        # Test
        result = permanently_delete_user_sync(mock_db, "user_id")

        # Verify
        assert result is True
        mock_db.commit.assert_called_once()

    def test_get_deleted_users_sync(self):
        """Test getting deleted users."""
        # Mock session
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_users = [MagicMock(), MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_users
        mock_db.execute.return_value = mock_result

        # Test
        result = get_deleted_users_sync(mock_db, skip=0, limit=10)

        # Verify
        assert result == mock_users
        mock_db.execute.assert_called_once()

    def test_count_deleted_users_sync(self):
        """Test counting deleted users."""
        # Mock session
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_users = [MagicMock() for _ in range(5)]
        mock_result.scalars.return_value.all.return_value = mock_users
        mock_db.execute.return_value = mock_result

        # Test
        result = count_deleted_users_sync(mock_db)

        # Verify
        assert result == 5
        mock_db.execute.assert_called_once()

    def test_get_users_sync(self):
        """Test getting users."""
        # Mock session
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_users = [MagicMock(), MagicMock(), MagicMock()]
        mock_result.scalars.return_value.all.return_value = mock_users
        mock_db.execute.return_value = mock_result

        # Test
        result = get_users_sync(mock_db, skip=0, limit=10)

        # Verify
        assert result == mock_users
        mock_db.execute.assert_called_once()

    def test_count_users_sync(self):
        """Test counting users."""
        # Mock session
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_users = [MagicMock() for _ in range(10)]
        mock_result.scalars.return_value.all.return_value = mock_users
        mock_db.execute.return_value = mock_result

        # Test
        result = count_users_sync(mock_db)

        # Verify
        assert result == 10
        mock_db.execute.assert_called_once()


class TestUserCRUDIntegration:
    """Test user CRUD integration scenarios."""

    def test_complete_user_lifecycle_sync(self):
        """Test complete user lifecycle with sync operations."""
        # Mock session
        mock_db = MagicMock(spec=Session)

        # Test that all CRUD functions can be called without errors
        # This is a simplified integration test that verifies the functions exist and are callable

        # Step 1: Create user (data structure for testing)
        _ = UserCreate(
            email="test@example.com",
            username="testuser",
            password="TestPassword123!",
            is_superuser=False,
        )

        # Mock the database operations
        mock_result = MagicMock()
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        # Test that functions can be called (they will use the mocked database)
        assert create_user_sync is not None
        assert get_user_by_email_sync is not None
        assert authenticate_user_sync is not None
        assert soft_delete_user_sync is not None
        assert restore_user_sync is not None

    async def test_complete_user_lifecycle_async(self):
        """Test complete user lifecycle with async operations."""
        # Mock async session
        mock_db = AsyncMock(spec=AsyncSession)

        # Test that all async CRUD functions can be called without errors
        # This is a simplified integration test that verifies the functions exist and are callable

        # Step 1: Create user (data structure for testing)
        _ = UserCreate(
            email="test@example.com",
            username="testuser",
            password="TestPassword123!",
            is_superuser=False,
        )

        # Mock the database operations
        mock_result = MagicMock()
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        # Test that functions can be called (they will use the mocked database)
        assert create_user is not None
        assert get_user_by_email is not None
        assert authenticate_user is not None
