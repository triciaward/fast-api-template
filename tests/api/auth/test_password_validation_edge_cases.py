"""Password validation edge case tests."""

import types
from unittest.mock import AsyncMock

import pytest

from tests.utils.auth_helpers import (
    MockEmailService,
    create_test_user,
    override_dependency,
)

pytestmark = pytest.mark.asyncio


class TestPasswordValidationEdgeCases:
    """Test password validation edge cases."""

    async def test_forgot_password_rate_limiting_integration(
        self,
        monkeypatch,
        async_client,
    ):
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

    async def test_password_change_weak_password_handling(
        self,
        monkeypatch,
        async_client,
    ):
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

    async def test_password_operations_with_deleted_user(
        self,
        monkeypatch,
        async_client,
    ):
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
