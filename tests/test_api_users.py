import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token


@pytest.mark.asyncio
class TestUserEndpoints:
    """Test user API endpoints."""

    async def test_get_current_user_success(self, client: TestClient, test_user_data: dict[str, str]) -> None:
        """Test successfully getting current user information."""
        # Create user via API instead of direct database access
        register_response = client.post(
            "/api/v1/auth/register", json=test_user_data)
        assert register_response.status_code == 200

        # Get the created user's email for token creation
        user_email = test_user_data["email"]

        # Create access token
        access_token = create_access_token(subject=user_email)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Get current user info
        response = client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Check response contains expected fields
        assert "id" in data
        assert "email" in data
        assert "username" in data
        assert "date_created" in data
        # Password should not be in response
        assert "password" not in data
        assert "hashed_password" not in data

        # Check values match user
        assert data["email"] == test_user_data["email"]
        assert data["username"] == test_user_data["username"]

    async def test_get_current_user_no_token(self, client: TestClient) -> None:
        """Test getting current user without authentication token."""
        response = client.get("/api/v1/users/me")

        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    async def test_get_current_user_invalid_token(self, client: TestClient) -> None:
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}

        response = client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]

    async def test_get_current_user_expired_token(self, client: TestClient, test_user_data: dict[str, str]) -> None:
        """Test getting current user with expired token."""
        # Create user via API
        register_response = client.post(
            "/api/v1/auth/register", json=test_user_data)
        assert register_response.status_code == 200

        user_email = test_user_data["email"]

        # Create expired token (negative expiration)
        from datetime import timedelta
        access_token = create_access_token(
            subject=user_email,
            expires_delta=timedelta(seconds=-1)
        )
        headers = {"Authorization": f"Bearer {access_token}"}

        # Try to get current user info with expired token
        response = client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]

    async def test_get_current_user_wrong_secret_key(self, client: TestClient, test_user_data: dict[str, str]) -> None:
        """Test getting current user with token signed by wrong secret key."""
        # Create user via API
        register_response = client.post(
            "/api/v1/auth/register", json=test_user_data)
        assert register_response.status_code == 200

        user_email = test_user_data["email"]

        # Create token with wrong secret (this simulates a tampered token)
        from datetime import datetime, timedelta

        from jose import jwt

        expire = datetime.utcnow() + timedelta(minutes=30)
        to_encode = {"exp": expire, "sub": str(user_email)}
        # Use wrong secret key
        malicious_token = jwt.encode(
            to_encode, "wrong_secret_key", algorithm="HS256")

        headers = {"Authorization": f"Bearer {malicious_token}"}

        response = client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]

    async def test_get_current_user_nonexistent_user(self, client: TestClient) -> None:
        """Test getting current user with token for non-existent user."""
        # Create token for non-existent user email
        access_token = create_access_token(subject="nonexistent@example.com")
        headers = {"Authorization": f"Bearer {access_token}"}

        response = client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]

    async def test_get_current_user_malformed_token(self, client: TestClient) -> None:
        """Test getting current user with malformed token."""
        headers = {"Authorization": "Bearer not.a.valid.jwt.token"}

        response = client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]

    async def test_get_current_user_wrong_auth_scheme(self, client: TestClient, test_user_data: dict[str, str]) -> None:
        """Test getting current user with wrong authentication scheme."""
        # Create user via API
        register_response = client.post(
            "/api/v1/auth/register", json=test_user_data)
        assert register_response.status_code == 200

        user_email = test_user_data["email"]

        # Create token
        access_token = create_access_token(subject=user_email)

        # Use wrong auth scheme (should be "Bearer")
        headers = {"Authorization": f"Basic {access_token}"}

        response = client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
