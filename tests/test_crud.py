import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import user as crud_user
from app.schemas.user import UserCreate


@pytest.mark.asyncio
class TestCRUD:
    """Test CRUD operations."""

    async def test_create_user(self, db_session: AsyncSession) -> None:
        """Test creating a user."""
        user_create = UserCreate(
            email="test@example.com",
            username="testuser",
            password="testpassword123",
            is_superuser=False,
        )
        user = await crud_user.create_user_async(db=db_session, user=user_create)

        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.hashed_password is not None
        assert user.hashed_password != "testpassword123"
        assert user.id is not None

    async def test_get_user_by_email(self, db_session: AsyncSession) -> None:
        """Test getting user by email."""
        user_create = UserCreate(
            email="test@example.com",
            username="testuser",
            password="testpassword123",
            is_superuser=False,
        )
        created_user = await crud_user.create_user_async(
            db=db_session, user=user_create
        )

        # Get user by email
        user = await crud_user.get_user_by_email_async(
            db=db_session, email="test@example.com"
        )
        assert user is not None
        assert user.email == "test@example.com"
        assert user.id == created_user.id

    async def test_get_user_by_email_nonexistent(
        self, db_session: AsyncSession
    ) -> None:
        """Test getting user by non-existent email."""
        user = await crud_user.get_user_by_email_async(
            db=db_session, email="nonexistent@example.com"
        )
        assert user is None

    async def test_get_user_by_username(self, db_session: AsyncSession) -> None:
        """Test getting user by username."""
        user_create = UserCreate(
            email="test@example.com",
            username="testuser",
            password="testpassword123",
            is_superuser=False,
        )
        created_user = await crud_user.create_user_async(
            db=db_session, user=user_create
        )

        # Get user by username
        user = await crud_user.get_user_by_username_async(
            db=db_session, username="testuser"
        )
        assert user is not None
        assert user.username == "testuser"
        assert user.id == created_user.id

    async def test_get_user_by_username_nonexistent(
        self, db_session: AsyncSession
    ) -> None:
        """Test getting user by non-existent username."""
        user = await crud_user.get_user_by_username_async(
            db=db_session, username="nonexistentuser"
        )
        assert user is None

    async def test_authenticate_user_success(self, db_session: AsyncSession) -> None:
        """Test successful user authentication."""
        user_create = UserCreate(
            email="test@example.com",
            username="testuser",
            password="testpassword123",
            is_superuser=False,
        )
        await crud_user.create_user_async(db=db_session, user=user_create)

        # Authenticate with correct credentials
        user = await crud_user.authenticate_user_async(
            db=db_session, email="test@example.com", password="testpassword123"
        )
        assert user is not None
        assert user.email == "test@example.com"

    async def test_authenticate_user_wrong_password(
        self, db_session: AsyncSession
    ) -> None:
        """Test login with wrong password."""
        user_create = UserCreate(
            email="test@example.com",
            username="testuser",
            password="testpassword123",
            is_superuser=False,
        )
        await crud_user.create_user_async(db=db_session, user=user_create)

        # Authenticate with wrong password
        user = await crud_user.authenticate_user_async(
            db=db_session, email="test@example.com", password="wrongpassword"
        )
        assert user is None

    async def test_authenticate_user_nonexistent(
        self, db_session: AsyncSession
    ) -> None:
        """Test authentication with non-existent user."""
        user = await crud_user.authenticate_user_async(
            db=db_session, email="nonexistent@example.com", password="anypassword"
        )
        assert user is None

    async def test_user_password_hashing(self, db_session: AsyncSession) -> None:
        """Test that user passwords are properly hashed."""
        user_create = UserCreate(
            email="test@example.com",
            username="testuser",
            password="testpassword123",
            is_superuser=False,
        )
        user = await crud_user.create_user_async(db=db_session, user=user_create)

        # Password should be hashed
        assert user.hashed_password != "testpassword123"
        assert len(user.hashed_password) > len("testpassword123")

    async def test_user_uuid_generation(self, db_session: AsyncSession) -> None:
        """Test that users get UUID primary keys."""
        user_create = UserCreate(
            email="test@example.com",
            username="testuser",
            password="testpassword123",
            is_superuser=False,
        )
        user = await crud_user.create_user_async(db=db_session, user=user_create)

        # ID should be a UUID
        assert user.id is not None
        # Check if it has UUID-like attributes
        assert hasattr(user.id, "hex")

    async def test_user_timestamp_generation(self, db_session: AsyncSession) -> None:
        """Test that users get creation timestamps."""
        user_create = UserCreate(
            email="test@example.com",
            username="testuser",
            password="testpassword123",
            is_superuser=False,
        )
        user = await crud_user.create_user_async(db=db_session, user=user_create)

        # Should have creation timestamp
        assert user.date_created is not None
