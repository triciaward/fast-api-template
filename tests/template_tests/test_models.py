import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.schemas.user import Token, TokenData, UserCreate, UserResponse

# mypy: disable-error-code="call-arg,unused-ignore"


class TestUserModel:
    """Test User database model."""

    @pytest.mark.asyncio
    async def test_user_model_creation(self, db_session: AsyncSession) -> None:
        """Test creating a User model instance."""
        user = User(
            email="test_model_creation@example.com",
            username="testuser_model_creation",
            hashed_password="hashed_password_123",
            is_superuser=False,
        )

        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Check that user was created with correct attributes
        assert str(user.email) == "test_model_creation@example.com"
        assert str(user.username) == "testuser_model_creation"
        assert str(user.hashed_password) == "hashed_password_123"
        # Handle both standard UUID and asyncpg UUID types
        assert hasattr(user.id, "hex")  # Both UUID types have hex attribute
        # Check date_created is not None and has datetime-like attributes
        assert user.date_created is not None
        assert hasattr(user.date_created, "year")
        assert hasattr(user.date_created, "month")
        assert hasattr(user.date_created, "day")

        # Test string representation
        repr_str = repr(user)
        assert "User(" in repr_str
        assert "test_model_creation@example.com" in repr_str
        assert "testuser_model_creation" in repr_str

    @pytest.mark.asyncio
    async def test_user_model_unique_email(self, db_session: AsyncSession) -> None:
        """Test that user emails must be unique."""
        # Create first user
        user1 = User(
            email="test_model_unique_email@example.com",
            username="testuser1_unique_email",
            hashed_password="hashed_password_123",
            is_superuser=False,
        )
        db_session.add(user1)
        await db_session.commit()

        # Try to create second user with same email
        user2 = User(
            email="test_model_unique_email@example.com",  # Same email
            username="testuser2_unique_email",
            hashed_password="hashed_password_456",
            is_superuser=False,
        )
        db_session.add(user2)

        # Should raise integrity error
        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_user_model_unique_username(self, db_session: AsyncSession) -> None:
        """Test that usernames must be unique."""
        # Create first user
        user1 = User(
            email="test1_model_unique_username@example.com",
            username="testuser_model_unique_username",
            hashed_password="hashed_password_123",
            is_superuser=False,
        )
        db_session.add(user1)
        await db_session.commit()

        # Try to create second user with same username
        user2 = User(
            email="test2_model_unique_username@example.com",
            username="testuser_model_unique_username",  # Same username
            hashed_password="hashed_password_456",
            is_superuser=False,
        )
        db_session.add(user2)

        # Should raise integrity error
        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_user_model_auto_generated_fields(
        self,
        db_session: AsyncSession,
    ) -> None:
        """Test that ID and date_created are auto-generated."""
        user = User(
            email="test_model_auto_generated@example.com",
            username="testuser_model_auto_generated",
            hashed_password="hashed_password_123",
            is_superuser=False,
        )

        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # After commit, all fields should be set and auto-generated
        # Handle both standard UUID and asyncpg UUID types
        assert hasattr(user.id, "hex")  # Both UUID types have hex attribute
        # Check date_created is not None and has datetime-like attributes
        assert user.date_created is not None
        assert hasattr(user.date_created, "year")
        assert hasattr(user.date_created, "month")
        assert hasattr(user.date_created, "day")
        # Verify these were auto-generated (not None)
        assert user.id is not None
        assert user.date_created is not None


class TestUserSchemas:
    """Test Pydantic schemas for user validation."""

    def test_user_create_schema_valid(self) -> None:
        """Test valid UserCreate schema."""
        user_create = UserCreate(
            email="test@example.com",
            username="testuser",
            password="TestPassword123!",
            is_superuser=False,
        )

        assert user_create.email == "test@example.com"
        assert user_create.username == "testuser"
        assert user_create.password == "TestPassword123!"
        assert user_create.is_superuser is False

    def test_user_create_schema_invalid_email(self) -> None:
        """Test UserCreate schema with invalid email."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="invalid-email",
                username="testuser",
                password="TestPassword123!",
                is_superuser=False,
            )

    def test_user_create_schema_missing_fields(self) -> None:
        """Test UserCreate schema with missing required fields."""
        # Test missing password - this should raise ValidationError
        with pytest.raises(ValidationError):
            UserCreate(email="test@example.com", username="testuser")

    def test_user_response_schema(self) -> None:
        """Test UserResponse schema."""
        user_id = uuid.uuid4()
        date_created = datetime.now(timezone.utc)

        user_response = UserResponse(
            id=user_id,
            email="test@example.com",
            username="testuser",
            is_superuser=False,
            is_verified=True,
            date_created=date_created,
        )

        assert user_response.id == user_id
        assert user_response.email == "test@example.com"
        assert user_response.username == "testuser"
        assert user_response.is_superuser is False
        assert user_response.is_verified is True
        assert user_response.date_created == date_created

    def test_token_schema(self) -> None:
        """Test Token schema."""
        token_data = {"access_token": "sample_jwt_token_123", "token_type": "bearer"}

        token = Token(**token_data)

        assert token.access_token == "sample_jwt_token_123"
        assert token.token_type == "bearer"

    def test_token_data_schema(self) -> None:
        """Test TokenData schema."""
        # Test with email
        token_data = TokenData(email="test@example.com")
        assert token_data.email == "test@example.com"

        # Test with None email (optional)
        token_data_none = TokenData(email=None)
        assert token_data_none.email is None

        # Test with no email provided (should default to None)
        token_data_default = TokenData()
        assert token_data_default.email is None
