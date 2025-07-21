import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.crud import user as crud_user
from app.schemas.user import UserCreate


@pytest.mark.skip(reason="Requires complex search functionality - not implemented yet")
def test_users_endpoint_with_search(client: TestClient, sync_db_session: Session):
    """Test the users endpoint with search functionality."""
    # Create test users
    user1 = crud_user.create_user_sync(
        sync_db_session,
        UserCreate(
            email="trish@example.com", username="trish_ward", password="Password123!"
        ),
    )
    _user2 = crud_user.create_user_sync(
        sync_db_session,
        UserCreate(
            email="john@example.com", username="john_doe", password="Password123!"
        ),
    )

    # Verify user1 so they can log in
    crud_user.verify_user_sync(sync_db_session, str(user1.id))

    # Login to get access token
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "trish@example.com", "password": "Password123!"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Test search
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/users?search=trish", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 1
    assert data["items"][0]["username"] == "trish_ward"


@pytest.mark.skip(reason="Requires complex search functionality - not implemented yet")
def test_users_endpoint_with_oauth_filter(client: TestClient, sync_db_session: Session):
    """Test the users endpoint with OAuth provider filter."""
    # Create test users
    user1 = crud_user.create_user_sync(
        sync_db_session,
        UserCreate(
            email="trish@example.com", username="trish_ward", password="Password123!"
        ),
    )
    _user2 = crud_user.create_user_sync(
        sync_db_session,
        UserCreate(
            email="john@example.com", username="john_doe", password="Password123!"
        ),
    )

    # Verify user1 so they can log in
    crud_user.verify_user_sync(sync_db_session, str(user1.id))

    # Login to get access token
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "trish@example.com", "password": "Password123!"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Test OAuth filter
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/users?oauth_provider=none", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    # Should return users with no OAuth provider (traditional email/password users)


@pytest.mark.skip(reason="Requires complex search functionality - not implemented yet")
def test_enhanced_search_endpoint(client: TestClient, sync_db_session: Session):
    """Test the enhanced search endpoint with metadata."""
    # Create test users
    user1 = crud_user.create_user_sync(
        sync_db_session,
        UserCreate(
            email="trish@example.com", username="trish_ward", password="Password123!"
        ),
    )
    _user2 = crud_user.create_user_sync(
        sync_db_session,
        UserCreate(
            email="john@example.com", username="john_doe", password="Password123!"
        ),
    )

    # Verify user1 so they can log in
    crud_user.verify_user_sync(sync_db_session, str(user1.id))

    # Login to get access token
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "trish@example.com", "password": "Password123!"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Test enhanced search endpoint
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(
        "/api/v1/users/search?search=trish&is_verified=true", headers=headers
    )

    assert response.status_code == 200
    data = response.json()

    # Check enhanced response structure
    assert "users" in data
    assert "total_count" in data
    assert "page" in data
    assert "per_page" in data
    assert "total_pages" in data
    assert "has_next" in data
    assert "has_prev" in data
    assert "search_applied" in data
    assert "filters_applied" in data
    assert "sort_field" in data
    assert "sort_order" in data

    # Check metadata values
    assert data["search_applied"] is True
    assert "text_search" in data["filters_applied"]
    assert "verification_status" in data["filters_applied"]
    assert len(data["users"]) >= 1
