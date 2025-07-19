"""Tests for superuser functionality."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.user import create_user, get_user_by_email
from app.schemas.user import UserCreate

# mypy: disable-error-code="unreachable"


@pytest.mark.asyncio
async def test_create_superuser(db_session: AsyncSession) -> None:
    """Test creating a superuser account."""
    # Create superuser data
    superuser_data = UserCreate(
        email="admin@test.com",
        username="superadmin",
        password="TestPassword123!",
        is_superuser=True,
    )

    # Create superuser
    superuser = await create_user(db_session, superuser_data)

    # Verify superuser was created correctly
    assert superuser.email == "admin@test.com"
    assert superuser.username == "superadmin"
    assert superuser.is_superuser is True

    # Verify we can retrieve the superuser
    retrieved_user = await get_user_by_email(db_session, "admin@test.com")
    assert retrieved_user is not None
    # Verify superuser status
    superuser_status = retrieved_user.is_superuser
    assert superuser_status is True


@pytest.mark.asyncio
async def test_create_regular_user(db_session: AsyncSession) -> None:
    """Test creating a regular user account."""
    # Create regular user data
    user_data = UserCreate(
        email="user@test.com",
        username="regularuser",
        password="TestPassword123!",
        is_superuser=False,
    )

    # Create user
    user = await create_user(db_session, user_data)

    # Verify user was created correctly
    assert user.email == "user@test.com"
    assert user.username == "regularuser"
    assert user.is_superuser is False

    # Verify we can retrieve the user
    retrieved_user = await get_user_by_email(db_session, "user@test.com")
    assert retrieved_user is not None
    # Verify user status
    user_status = retrieved_user.is_superuser
    assert user_status is False


@pytest.mark.asyncio
async def test_superuser_default_value(db_session: AsyncSession) -> None:
    """Test that is_superuser defaults to False when not specified."""
    # Create user data without specifying is_superuser
    user_data = UserCreate(
        email="default@test.com", username="defaultuser", password="TestPassword123!"
    )

    # Create user
    user = await create_user(db_session, user_data)

    # Verify is_superuser defaults to False
    assert user.is_superuser is False
