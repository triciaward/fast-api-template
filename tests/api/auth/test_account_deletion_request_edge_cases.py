"""Account deletion request edge case tests."""

import types
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from tests.utils.auth_helpers import MockEmailService

pytestmark = pytest.mark.asyncio


class TestAccountDeletionRequestEdgeCases:
    """Test edge cases for account deletion request functionality."""

    async def test_request_deletion_email_service_not_configured(self, async_client):
        """Test deletion request when email service is not configured."""
        from app.api.auth import account_deletion as mod

        mock_user = types.SimpleNamespace(
            id="test-id",
            email="test@example.com",
            is_deleted=False,
            deletion_requested_at=None,
        )

        async def mock_get_user(db, email):
            return mock_user

        # Mock unconfigured email service
        mock_email_service = None

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(mod.crud_user, "get_user_by_email", mock_get_user)
            mp.setattr(mod, "email_service", mock_email_service)

            resp = await async_client.post(
                "/api/auth/request-deletion",
                json={"email": "test@example.com"},
            )

            assert resp.status_code == 200
            data = resp.json()
            assert "service temporarily unavailable" in data["message"].lower()
            assert data["email_sent"] is False

    async def test_request_deletion_token_creation_fails(self, async_client):
        """Test deletion request when token creation fails."""
        from app.api.auth import account_deletion as mod

        mock_user = types.SimpleNamespace(
            id="test-id",
            email="test@example.com",
            is_deleted=False,
            deletion_requested_at=None,
        )

        async def mock_get_user(db, email):
            return mock_user

        # Mock email service that fails to create token
        mock_email_service = MockEmailService(configured=True)
        mock_email_service.create_deletion_token = AsyncMock(return_value=None)

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(mod.crud_user, "get_user_by_email", mock_get_user)
            mp.setattr(mod, "email_service", mock_email_service)

            resp = await async_client.post(
                "/api/auth/request-deletion",
                json={"email": "test@example.com"},
            )

            assert resp.status_code == 200
            data = resp.json()
            assert "Failed to create deletion token" in data["message"]
            assert data["email_sent"] is False

    async def test_request_deletion_marking_fails(self, async_client):
        """Test deletion request when marking for deletion fails."""
        from app.api.auth import account_deletion as mod

        mock_user = types.SimpleNamespace(
            id="test-id",
            email="test@example.com",
            is_deleted=False,
            deletion_requested_at=None,
        )

        async def mock_get_user(db, email):
            return mock_user

        async def mock_request_deletion(db, user_id):
            return False  # Simulate failure

        mock_email_service = MockEmailService(configured=True)
        mock_email_service.create_deletion_token = AsyncMock(return_value="token123")

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(mod.crud_user, "get_user_by_email", mock_get_user)
            mp.setattr(mod.crud_user, "request_account_deletion", mock_request_deletion)
            mp.setattr(mod, "email_service", mock_email_service)

            resp = await async_client.post(
                "/api/auth/request-deletion",
                json={"email": "test@example.com"},
            )

            assert resp.status_code == 200
            data = resp.json()
            assert "Failed to process deletion request" in data["message"]
            assert data["email_sent"] is False

    async def test_request_deletion_email_send_fails(self, async_client):
        """Test deletion request when email sending fails."""
        from app.api.auth import account_deletion as mod

        mock_user = types.SimpleNamespace(
            id="test-id",
            email="test@example.com",
            username="testuser",
            is_deleted=False,
            deletion_requested_at=None,
        )

        async def mock_get_user(db, email):
            return mock_user

        async def mock_request_deletion(db, user_id):
            return True

        async def mock_log_deletion(db, request, user, deletion_stage):
            pass  # Mock audit logging

        mock_email_service = MockEmailService(configured=True)
        mock_email_service.create_deletion_token = AsyncMock(return_value="token123")
        mock_email_service.send_account_deletion_email = (
            lambda *args: False
        )  # Fail to send

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(mod.crud_user, "get_user_by_email", mock_get_user)
            mp.setattr(mod.crud_user, "request_account_deletion", mock_request_deletion)
            mp.setattr(mod, "email_service", mock_email_service)
            mp.setattr(mod, "log_account_deletion", mock_log_deletion)

            resp = await async_client.post(
                "/api/auth/request-deletion",
                json={"email": "test@example.com"},
            )

            assert resp.status_code == 200
            data = resp.json()
            assert "Failed to send deletion confirmation email" in data["message"]
            assert data["email_sent"] is False

    async def test_request_deletion_already_deleted_user(self, async_client):
        """Test deletion request for already deleted user."""
        from app.api.auth import account_deletion as mod

        mock_user = types.SimpleNamespace(
            id="test-id",
            email="test@example.com",
            is_deleted=True,  # Already deleted
            deletion_requested_at=None,
        )

        async def mock_get_user(db, email):
            return mock_user

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(mod.crud_user, "get_user_by_email", mock_get_user)

            resp = await async_client.post(
                "/api/auth/request-deletion",
                json={"email": "test@example.com"},
            )

            assert resp.status_code == 200
            data = resp.json()
            assert "If an account with that email exists" in data["message"]
            assert data["email_sent"] is True  # Security - don't reveal user state

    async def test_request_deletion_already_requested(self, async_client):
        """Test deletion request when deletion is already requested."""
        from app.api.auth import account_deletion as mod

        mock_user = types.SimpleNamespace(
            id="test-id",
            email="test@example.com",
            is_deleted=False,
            deletion_requested_at=datetime.now(timezone.utc),  # Already requested
        )

        async def mock_get_user(db, email):
            return mock_user

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(mod.crud_user, "get_user_by_email", mock_get_user)

            resp = await async_client.post(
                "/api/auth/request-deletion",
                json={"email": "test@example.com"},
            )

            assert resp.status_code == 200
            data = resp.json()
            assert "If an account with that email exists" in data["message"]
            assert data["email_sent"] is True

    async def test_request_deletion_unexpected_error(self, async_client):
        """Test deletion request with unexpected error."""
        from app.api.auth import account_deletion as mod

        async def error_function(*args, **kwargs):
            raise Exception("Database connection error")

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(mod.crud_user, "get_user_by_email", error_function)

            resp = await async_client.post(
                "/api/auth/request-deletion",
                json={"email": "test@example.com"},
            )

            assert resp.status_code == 200
            data = resp.json()
            assert "deletion request failed" in data["message"].lower()
            assert data["email_sent"] is False
