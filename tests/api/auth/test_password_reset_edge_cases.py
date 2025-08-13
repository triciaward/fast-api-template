"""Password reset edge case tests."""

import types
from unittest.mock import AsyncMock

import pytest

from tests.utils.auth_helpers import MockEmailService

pytestmark = pytest.mark.asyncio


class TestPasswordResetEdgeCases:
    """Test edge cases for password reset functionality."""

    async def test_forgot_password_email_creation_fails(
        self,
        monkeypatch,
        async_client,
    ):
        """Test forgot password when email token creation fails."""
        from app.api.auth import password_management as mod

        mock_user = types.SimpleNamespace(
            id="test-id",
            email="test@example.com",
            oauth_provider=None,
        )

        # Mock email service that fails to create token
        mock_email_service = MockEmailService(configured=True)
        mock_email_service.create_password_reset_token = AsyncMock(return_value=None)

        async def mock_get_user(db, email):
            return mock_user

        monkeypatch.setattr(mod.crud_user, "get_user_by_email", mock_get_user)
        monkeypatch.setattr(mod, "email_service", mock_email_service)

        resp = await async_client.post(
            "/api/auth/forgot-password",
            json={"email": "test@example.com"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "Failed to create password reset token" in data["message"]
        assert data["email_sent"] is False

    async def test_forgot_password_email_send_fails(self, monkeypatch, async_client):
        """Test forgot password when email sending fails."""
        from app.api.auth import password_management as mod

        mock_user = types.SimpleNamespace(
            id="test-id",
            email="test@example.com",
            username="testuser",
            oauth_provider=None,
        )

        # Mock email service that creates token but fails to send
        mock_email_service = MockEmailService(configured=True)
        mock_email_service.create_password_reset_token = AsyncMock(
            return_value="token123",
        )
        mock_email_service.send_password_reset_email = lambda *args: False

        async def mock_get_user(db, email):
            return mock_user

        monkeypatch.setattr(mod.crud_user, "get_user_by_email", mock_get_user)
        monkeypatch.setattr(mod, "email_service", mock_email_service)

        resp = await async_client.post(
            "/api/auth/forgot-password",
            json={"email": "test@example.com"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "Failed to send password reset email" in data["message"]
        assert data["email_sent"] is False

    async def test_forgot_password_unexpected_error(self, monkeypatch, async_client):
        """Test forgot password with unexpected error."""
        from app.api.auth import password_management as mod

        async def error_function(*args, **kwargs):
            raise Exception("Unexpected database error")

        monkeypatch.setattr(mod.crud_user, "get_user_by_email", error_function)

        resp = await async_client.post(
            "/api/auth/forgot-password",
            json={"email": "test@example.com"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "failed" in data["message"].lower()
        assert data["email_sent"] is False

    async def test_reset_password_token_validation_fails(
        self,
        monkeypatch,
        async_client,
    ):
        """Test reset password with invalid token format."""
        from app.api.auth import password_management as mod

        # Mock that token validation fails
        mock_email_service = MockEmailService(configured=True)
        mock_email_service.verify_password_reset_token = AsyncMock(return_value=None)
        monkeypatch.setattr(mod, "email_service", mock_email_service)

        resp = await async_client.post(
            "/api/auth/reset-password",
            json={"token": "invalid-token", "new_password": "NewPassword123!"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "Invalid or expired" in data["message"]
        assert data["password_reset"] is False

    async def test_reset_password_user_not_found(self, monkeypatch, async_client):
        """Test reset password when user is not found by token."""
        from app.api.auth import password_management as mod

        # Mock that token is valid but user is not found
        mock_email_service = MockEmailService(configured=True)
        mock_email_service.verify_password_reset_token = AsyncMock(
            return_value="user-id",
        )
        monkeypatch.setattr(mod, "email_service", mock_email_service)

        async def mock_get_user_by_id(db, user_id):
            return None

        monkeypatch.setattr(mod.crud_user, "get_user_by_id", mock_get_user_by_id)

        resp = await async_client.post(
            "/api/auth/reset-password",
            json={"token": "valid-token", "new_password": "NewPassword123!"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "User not found" in data["message"]
        assert data["password_reset"] is False

    async def test_reset_password_oauth_user(self, monkeypatch, async_client):
        """Test reset password attempt for OAuth user."""
        from app.api.auth import password_management as mod

        mock_user = types.SimpleNamespace(
            id="test-id",
            email="test@example.com",
            oauth_provider="google",
        )

        # Mock email service to return a valid user ID
        mock_email_service = MockEmailService(configured=True)
        mock_email_service.verify_password_reset_token = AsyncMock(
            return_value="user-id",
        )
        monkeypatch.setattr(mod, "email_service", mock_email_service)

        async def mock_get_user_by_id(db, user_id):
            return mock_user

        monkeypatch.setattr(mod.crud_user, "get_user_by_id", mock_get_user_by_id)

        resp = await async_client.post(
            "/api/auth/reset-password",
            json={"token": "valid-token", "new_password": "NewPassword123!"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "Invalid or expired" in data["message"]
        assert data["password_reset"] is False

    async def test_reset_password_update_fails(self, monkeypatch, async_client):
        """Test reset password when password update fails."""
        from app.api.auth import password_management as mod

        mock_user = types.SimpleNamespace(
            id="test-id",
            email="test@example.com",
            username="testuser",
            oauth_provider=None,
        )

        mock_email_service = MockEmailService(configured=True)
        mock_email_service.verify_password_reset_token = AsyncMock(
            return_value="user-id",
        )
        monkeypatch.setattr(mod, "email_service", mock_email_service)

        async def mock_get_user_by_id(db, user_id):
            return mock_user

        async def mock_reset_password(db, user_id, password):
            return False

        monkeypatch.setattr(mod.crud_user, "get_user_by_id", mock_get_user_by_id)
        monkeypatch.setattr(mod.crud_user, "reset_user_password", mock_reset_password)

        resp = await async_client.post(
            "/api/auth/reset-password",
            json={"token": "valid-token", "new_password": "NewPassword123!"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "Failed to reset password" in data["message"]
        assert data["password_reset"] is False

    async def test_reset_password_unexpected_error(self, monkeypatch, async_client):
        """Test reset password with unexpected error."""
        from app.api.auth import password_management as mod

        async def error_function(*args, **kwargs):
            raise Exception("Database connection error")

        mock_email_service = MockEmailService(configured=True)
        mock_email_service.verify_password_reset_token = error_function
        monkeypatch.setattr(mod, "email_service", mock_email_service)

        resp = await async_client.post(
            "/api/auth/reset-password",
            json={"token": "valid-token", "new_password": "NewPassword123!"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "invalid or expired" in data["message"].lower()
        assert data["password_reset"] is False
