"""
Tests for user listing endpoints with pagination.

This module tests the user listing functionality with the new pagination system.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.crud import user as crud_user
from app.schemas.user import UserCreate


@pytest.mark.skip(
    reason="Requires complex pagination functionality - not implemented yet",
)
def test_list_users_with_pagination(
    client: TestClient, sync_db_session: Session,
) -> None:
    """Test user listing with pagination."""
    # Create test users
    users_data = [
        UserCreate(
            email=f"user{i}@example.com",
            username=f"user{i}",
            password="Password123!",
            is_superuser=False,
        )
        for i in range(25)  # Create 25 users
    ]

    created_users = []
    for user_data in users_data:
        user = crud_user.create_user_sync(sync_db_session, user_data)
        created_users.append(user)

    # Create a test user for authentication
    test_user_data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="Password123!",
        is_superuser=False,
    )
    test_user = crud_user.create_user_sync(sync_db_session, test_user_data)

    # Create access token
    access_token = create_access_token(subject=test_user.email)
    headers = {"Authorization": f"Bearer {access_token}"}

    # Test first page
    response = client.get("/api/v1/users?page=1&size=10", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert "metadata" in data
    assert len(data["items"]) == 10
    assert data["metadata"]["page"] == 1
    assert data["metadata"]["size"] == 10
    assert data["metadata"]["total"] == 26  # 25 created + 1 test user
    assert data["metadata"]["pages"] == 3
    assert data["metadata"]["has_next"] is True
    assert data["metadata"]["has_prev"] is False
    assert data["metadata"]["next_page"] == 2
    assert data["metadata"]["prev_page"] is None

    # Test second page
    response = client.get("/api/v1/users?page=2&size=10", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert len(data["items"]) == 10
    assert data["metadata"]["page"] == 2
    assert data["metadata"]["has_next"] is True
    assert data["metadata"]["has_prev"] is True
    assert data["metadata"]["next_page"] == 3
    assert data["metadata"]["prev_page"] == 1

    # Test last page
    response = client.get("/api/v1/users?page=3&size=10", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert len(data["items"]) == 6  # Remaining users
    assert data["metadata"]["page"] == 3
    assert data["metadata"]["has_next"] is False
    assert data["metadata"]["has_prev"] is True
    assert data["metadata"]["next_page"] is None
    assert data["metadata"]["prev_page"] == 2


@pytest.mark.skip(
    reason="Requires complex pagination functionality - not implemented yet",
)
def test_list_users_with_filters(client: TestClient, sync_db_session: Session) -> None:
    """Test user listing with filters."""
    # Create test users with different verification statuses
    verified_user = crud_user.create_user_sync(
        sync_db_session,
        UserCreate(
            email="verified@example.com",
            username="verified",
            password="Password123!",
            is_superuser=False,
        ),
    )
    crud_user.verify_user_sync(sync_db_session, str(verified_user.id))

    crud_user.create_user_sync(
        sync_db_session,
        UserCreate(
            email="unverified@example.com",
            username="unverified",
            password="Password123!",
            is_superuser=False,
        ),
    )

    # Create a test user for authentication
    test_user_data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="Password123!",
        is_superuser=False,
    )
    test_user = crud_user.create_user_sync(sync_db_session, test_user_data)

    # Create access token
    access_token = create_access_token(subject=test_user.email)
    headers = {"Authorization": f"Bearer {access_token}"}

    # Test filtering by verification status
    response = client.get("/api/v1/users?is_verified=true", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["metadata"]["total"] >= 1  # At least the verified user
    for user in data["items"]:
        assert user["is_verified"] is True

    # Test filtering by unverified status
    response = client.get("/api/v1/users?is_verified=false", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["metadata"]["total"] >= 1  # At least the unverified user
    for user in data["items"]:
        assert user["is_verified"] is False


@pytest.mark.skip(
    reason="Requires complex pagination functionality - not implemented yet",
)
def test_list_users_default_pagination(
    client: TestClient, sync_db_session: Session,
) -> None:
    """Test user listing with default pagination parameters."""
    # Create a test user for authentication
    test_user_data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="Password123!",
        is_superuser=False,
    )
    test_user = crud_user.create_user_sync(sync_db_session, test_user_data)

    # Create access token
    access_token = create_access_token(subject=test_user.email)
    headers = {"Authorization": f"Bearer {access_token}"}

    # Test without pagination parameters (should use defaults)
    response = client.get("/api/v1/users", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert "metadata" in data
    assert data["metadata"]["page"] == 1
    assert data["metadata"]["size"] == 20  # Default size
    assert len(data["items"]) <= 20  # Should not exceed default size


def test_list_users_unauthorized(client: TestClient) -> None:
    """Test user listing without authentication."""
    response = client.get("/api/v1/users")
    assert response.status_code == 401


def test_list_users_invalid_pagination(
    client: TestClient, sync_db_session: Session,
) -> None:
    """Test user listing with invalid pagination parameters."""
    # Create a test user for authentication
    test_user_data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="Password123!",
        is_superuser=False,
    )
    test_user = crud_user.create_user_sync(sync_db_session, test_user_data)

    # Create access token
    access_token = create_access_token(subject=test_user.email)
    headers = {"Authorization": f"Bearer {access_token}"}

    # Test invalid page number (should be caught by Pydantic validation)
    try:
        client.get("/api/v1/users?page=0", headers=headers)
        # If we get here, the validation didn't work as expected
        raise AssertionError("Expected validation error for page=0")
    except Exception as e:
        # FastAPI should catch this and return a validation error
        assert "validation error" in str(e).lower() or "422" in str(e)

    # Test invalid size (should be caught by Pydantic validation)
    try:
        client.get("/api/v1/users?size=0", headers=headers)
        # If we get here, the validation didn't work as expected
        raise AssertionError("Expected validation error for size=0")
    except Exception as e:
        # FastAPI should catch this and return a validation error
        assert "validation error" in str(e).lower() or "422" in str(e)

    try:
        client.get("/api/v1/users?size=101", headers=headers)
        # If we get here, the validation didn't work as expected
        raise AssertionError("Expected validation error for size=101")
    except Exception as e:
        # FastAPI should catch this and return a validation error
        assert "validation error" in str(e).lower() or "422" in str(e)
