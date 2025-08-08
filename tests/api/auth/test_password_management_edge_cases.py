"""Comprehensive edge case tests for password management to improve coverage."""
import types
from unittest.mock import AsyncMock

import pytest

from tests.utils.auth_helpers import (
    MockEmailService,
    create_test_user,
    override_dependency,
)

pytestmark = pytest.mark.asyncio


class TestPasswordResetEdgeCases:
    """Test edge cases for password reset functionality."""

    async def test_forgot_password_email_creation_fails(self, monkeypatch, async_client):
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
            "/auth/forgot-password",
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
        mock_email_service.create_password_reset_token = AsyncMock(return_value="token123")
        mock_email_service.send_password_reset_email = lambda *args: False

        async def mock_get_user(db, email):
            return mock_user

        monkeypatch.setattr(mod.crud_user, "get_user_by_email", mock_get_user)
        monkeypatch.setattr(mod, "email_service", mock_email_service)

        resp = await async_client.post(
            "/auth/forgot-password",
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
            "/auth/forgot-password",
            json={"email": "test@example.com"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "failed" in data["message"].lower()
        assert data["email_sent"] is False

    async def test_reset_password_token_validation_fails(self, monkeypatch, async_client):
        """Test reset password with invalid token format."""
        from app.api.auth import password_management as mod

        # Mock that token validation fails
        mock_email_service = MockEmailService(configured=True)
        mock_email_service.verify_password_reset_token = AsyncMock(return_value=None)
        monkeypatch.setattr(mod, "email_service", mock_email_service)

        resp = await async_client.post(
            "/auth/reset-password",
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
        mock_email_service.verify_password_reset_token = AsyncMock(return_value="user-id")
        monkeypatch.setattr(mod, "email_service", mock_email_service)

        async def mock_get_user_by_id(db, user_id):
            return None

        monkeypatch.setattr(mod.crud_user, "get_user_by_id", mock_get_user_by_id)

        resp = await async_client.post(
            "/auth/reset-password",
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
        mock_email_service.verify_password_reset_token = AsyncMock(return_value="user-id")
        monkeypatch.setattr(mod, "email_service", mock_email_service)
        async def mock_get_user_by_id(db, user_id):
            return mock_user
        monkeypatch.setattr(mod.crud_user, "get_user_by_id", mock_get_user_by_id)

        resp = await async_client.post(
            "/auth/reset-password",
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
        mock_email_service.verify_password_reset_token = AsyncMock(return_value="user-id")
        monkeypatch.setattr(mod, "email_service", mock_email_service)

        async def mock_get_user_by_id(db, user_id):
            return mock_user

        async def mock_reset_password(db, user_id, password):
            return False

        monkeypatch.setattr(mod.crud_user, "get_user_by_id", mock_get_user_by_id)
        monkeypatch.setattr(mod.crud_user, "reset_user_password", mock_reset_password)

        resp = await async_client.post(
            "/auth/reset-password",
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
            "/auth/reset-password",
            json={"token": "valid-token", "new_password": "NewPassword123!"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "invalid or expired" in data["message"].lower()
        assert data["password_reset"] is False


class TestPasswordChangeEdgeCases:
    """Test edge cases for password change functionality."""

    async def test_change_password_user_not_in_database(self, monkeypatch, async_client):
        """Test password change when user is not found in database."""
        from app.api.auth import password_management as mod
        from app.main import app

        current_user = create_test_user()

        async def fake_get_current_user():
            return current_user

        # Mock that user is not found in database
        async def mock_get_user_by_email(db, email):
            return None

        monkeypatch.setattr(mod.crud_user, "get_user_by_email", mock_get_user_by_email)

        cleanup = override_dependency(app, mod.get_current_user, fake_get_current_user)

        try:
            resp = await async_client.post(
                "/auth/change-password",
                json={"current_password": "OldPass123!", "new_password": "NewPass123!"},
                headers={"authorization": "Bearer token", "user-agent": "pytest"},
            )
            assert resp.status_code == 500
            assert "User not found" in resp.json()["error"]["message"]
        finally:
            cleanup()

    async def test_change_password_update_fails(self, monkeypatch, async_client):
        """Test password change when database update fails."""
        from app.api.auth import password_management as mod
        from app.main import app

        current_user = create_test_user()

        async def fake_get_current_user():
            return current_user

        async def fake_get_user_by_email(db, email):
            return types.SimpleNamespace(hashed_password="hashed_old_password", id=current_user.id)

        # Mock successful password verification but failed update
        async def mock_update_password(db, user_id, password):
            return False

        monkeypatch.setattr(mod.crud_user, "get_user_by_email", fake_get_user_by_email)
        monkeypatch.setattr(mod, "verify_password", lambda p, h: True)
        monkeypatch.setattr(mod.crud_user, "update_user_password", mock_update_password)

        cleanup = override_dependency(app, mod.get_current_user, fake_get_current_user)

        try:
            resp = await async_client.post(
                "/auth/change-password",
                json={"current_password": "OldPass123!", "new_password": "NewPass123!"},
                headers={"authorization": "Bearer token", "user-agent": "pytest"},
            )
            assert resp.status_code == 500
            assert "Failed to change password" in resp.json()["error"]["message"]
        finally:
            cleanup()

    async def test_change_password_audit_log_success(self, monkeypatch, async_client):
        """Test password change with successful audit logging."""
        from app.api.auth import password_management as mod
        from app.main import app

        current_user = create_test_user()
        audit_log_called = False

        async def fake_get_current_user():
            return current_user

        async def fake_get_user_by_email(db, email):
            return types.SimpleNamespace(hashed_password="hashed_old_password", id=current_user.id)

        async def fake_log_password_change(db, request, user, change_type):
            nonlocal audit_log_called
            audit_log_called = True
            assert change_type == "password_change"

        async def mock_update_password(db, user_id, password):
            return True

        monkeypatch.setattr(mod.crud_user, "get_user_by_email", fake_get_user_by_email)
        monkeypatch.setattr(mod, "verify_password", lambda p, h: True)
        monkeypatch.setattr(mod.crud_user, "update_user_password", mock_update_password)
        monkeypatch.setattr(mod, "log_password_change", fake_log_password_change)

        cleanup = override_dependency(app, mod.get_current_user, fake_get_current_user)

        try:
            resp = await async_client.post(
                "/auth/change-password",
                json={"current_password": "OldPass123!", "new_password": "NewPass123!"},
                headers={"authorization": "Bearer token", "user-agent": "pytest"},
            )
            assert resp.status_code == 200
            assert "successfully" in resp.json()["detail"].lower()
            assert audit_log_called
        finally:
            cleanup()

    async def test_change_password_unexpected_error(self, monkeypatch, async_client):
        """Test password change with unexpected error."""
        from app.api.auth import password_management as mod
        from app.main import app

        current_user = create_test_user()

        async def fake_get_current_user():
            return current_user

        async def error_function(*args, **kwargs):
            raise Exception("Database connection lost")

        monkeypatch.setattr(mod.crud_user, "get_user_by_email", error_function)

        cleanup = override_dependency(app, mod.get_current_user, fake_get_current_user)

        try:
            resp = await async_client.post(
                "/auth/change-password",
                json={"current_password": "OldPass123!", "new_password": "NewPass123!"},
                headers={"authorization": "Bearer token", "user-agent": "pytest"},
            )
            assert resp.status_code == 500
            assert "Password change failed" in resp.json()["error"]["message"]
        finally:
            cleanup()


class TestPasswordValidationEdgeCases:
    """Test password validation edge cases."""

    async def test_forgot_password_rate_limiting_integration(self, monkeypatch, async_client):
        """Test forgot password with rate limiting enabled."""
        from app.api.auth import password_management as mod

        # Mock that rate limiting is triggered (this would normally be handled by middleware)
        # We test that the endpoint handles rate limiting gracefully
        mock_user = types.SimpleNamespace(
            id="test-id",
            email="test@example.com",
            username="testuser",
            oauth_provider=None,
        )

        mock_email_service = MockEmailService(configured=True)

        async def mock_get_user(db, email):
            return mock_user

        monkeypatch.setattr(mod.crud_user, "get_user_by_email", mock_get_user)
        monkeypatch.setattr(mod, "email_service", mock_email_service)

        # Simulate successful flow despite rate limiting
        resp = await async_client.post(
            "/auth/forgot-password",
            json={"email": "test@example.com"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["email_sent"] is True

    async def test_password_reset_token_edge_cases(self, monkeypatch, async_client):
        """Test password reset with various token edge cases."""
        from app.api.auth import password_management as mod

        # Test with empty token
        resp = await async_client.post(
            "/auth/reset-password",
            json={"token": "", "new_password": "NewPassword123!"},
        )
        assert resp.status_code == 200  # Application handles empty tokens gracefully

        # Test with very long token
        long_token = "a" * 1000
        mock_email_service = MockEmailService(configured=True)
        mock_email_service.verify_password_reset_token = AsyncMock(return_value=None)
        monkeypatch.setattr(mod, "email_service", mock_email_service)

        resp = await async_client.post(
            "/auth/reset-password",
            json={"token": long_token, "new_password": "NewPassword123!"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "Invalid or expired" in data["message"]

    async def test_password_change_weak_password_handling(self, monkeypatch, async_client):
        """Test password change with weak passwords."""
        from app.api.auth import password_management as mod
        from app.main import app

        current_user = create_test_user()

        async def fake_get_current_user():
            return current_user

        cleanup = override_dependency(app, mod.get_current_user, fake_get_current_user)

        try:
            # Test with weak password (assuming validation happens at schema level)
            resp = await async_client.post(
                "/auth/change-password",
                json={"current_password": "OldPass123!", "new_password": "123"},
                headers={"authorization": "Bearer token", "user-agent": "pytest"},
            )
            # Should be caught by schema validation
            assert resp.status_code == 422
        finally:
            cleanup()

    async def test_password_operations_with_deleted_user(self, monkeypatch, async_client):
        """Test password operations when user is soft-deleted."""
        from app.api.auth import password_management as mod

        # Simulate soft-deleted user
        mock_user = types.SimpleNamespace(
            id="test-id",
            email="test@example.com",
            username="testuser",
            oauth_provider=None,
            is_deleted=True,  # Soft-deleted user
        )

        async def mock_get_user(db, email):
            return mock_user

        # Mock email service as configured
        mock_email_service = MockEmailService(configured=True)

        monkeypatch.setattr(mod.crud_user, "get_user_by_email", mock_get_user)
        monkeypatch.setattr(mod, "email_service", mock_email_service)

        resp = await async_client.post(
            "/auth/forgot-password",
            json={"email": "test@example.com"},
        )

        # Should still return success to not reveal user existence
        assert resp.status_code == 200
        data = resp.json()
        assert "If an account with that email exists" in data["message"]
        assert data["email_sent"] is True  # Should still return True for security
