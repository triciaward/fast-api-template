"""Account deletion confirmation edge case tests."""

import types
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from tests.utils.auth_helpers import MockEmailService

pytestmark = pytest.mark.asyncio


class TestAccountDeletionConfirmEdgeCases:
    """Test edge cases for account deletion confirmation functionality."""

    async def test_confirm_deletion_email_service_not_configured(self, async_client):
        """Test deletion confirmation when email service is not configured."""
        from app.api.auth import account_deletion as mod

        # Mock unconfigured email service
        mock_email_service = None

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(mod, "email_service", mock_email_service)

            resp = await async_client.post(
                "/api/auth/confirm-deletion",
                json={"token": "test-token"},
            )

            assert resp.status_code == 200
            data = resp.json()
            assert "service temporarily unavailable" in data["message"].lower()
            assert data["deletion_confirmed"] is False

    async def test_confirm_deletion_invalid_token(self, async_client):
        """Test deletion confirmation with invalid token."""
        from app.api.auth import account_deletion as mod

        mock_email_service = MockEmailService(configured=True)
        mock_email_service.verify_deletion_token = AsyncMock(return_value=None)

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(mod, "email_service", mock_email_service)

            resp = await async_client.post(
                "/api/auth/confirm-deletion",
                json={"token": "invalid-token"},
            )

            assert resp.status_code == 200
            data = resp.json()
            assert "Invalid or expired deletion token" in data["message"]
            assert data["deletion_confirmed"] is False

    async def test_confirm_deletion_user_not_found(self, async_client):
        """Test deletion confirmation when user is not found."""
        from app.api.auth import account_deletion as mod

        async def mock_get_user_by_id(db, user_id):
            return None

        mock_email_service = MockEmailService(configured=True)
        mock_email_service.verify_deletion_token = AsyncMock(return_value="user-id")

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(mod, "email_service", mock_email_service)
            mp.setattr(mod.crud_user, "get_user_by_id", mock_get_user_by_id)

            resp = await async_client.post(
                "/api/auth/confirm-deletion",
                json={"token": "valid-token"},
            )

            assert resp.status_code == 200
            data = resp.json()
            assert "User not found" in data["message"]
            assert data["deletion_confirmed"] is False

    async def test_confirm_deletion_already_deleted_user(self, async_client):
        """Test deletion confirmation for already deleted user."""
        from app.api.auth import account_deletion as mod

        mock_user = types.SimpleNamespace(
            id="test-id",
            email="test@example.com",
            is_deleted=True,  # Already deleted
        )

        async def mock_get_user_by_id(db, user_id):
            return mock_user

        mock_email_service = MockEmailService(configured=True)
        mock_email_service.verify_deletion_token = AsyncMock(return_value="user-id")

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(mod, "email_service", mock_email_service)
            mp.setattr(mod.crud_user, "get_user_by_id", mock_get_user_by_id)

            resp = await async_client.post(
                "/api/auth/confirm-deletion",
                json={"token": "valid-token"},
            )

            assert resp.status_code == 200
            data = resp.json()
            assert "Account has already been deleted" in data["message"]
            assert data["deletion_confirmed"] is False

    async def test_confirm_deletion_confirmation_fails(self, async_client):
        """Test deletion confirmation when confirmation process fails."""
        from app.api.auth import account_deletion as mod

        mock_user = types.SimpleNamespace(
            id="test-id",
            email="test@example.com",
            is_deleted=False,
        )

        async def mock_get_user_by_id(db, user_id):
            return mock_user

        async def mock_confirm_deletion(db, user_id):
            return False  # Simulate failure

        mock_email_service = MockEmailService(configured=True)
        mock_email_service.verify_deletion_token = AsyncMock(return_value="user-id")

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(mod, "email_service", mock_email_service)
            mp.setattr(mod.crud_user, "get_user_by_id", mock_get_user_by_id)
            mp.setattr(mod.crud_user, "confirm_account_deletion", mock_confirm_deletion)

            resp = await async_client.post(
                "/api/auth/confirm-deletion",
                json={"token": "valid-token"},
            )

            assert resp.status_code == 200
            data = resp.json()
            assert "Failed to confirm account deletion" in data["message"]
            assert data["deletion_confirmed"] is False

    async def test_confirm_deletion_success_with_grace_period(self, async_client):
        """Test successful deletion confirmation with grace period."""
        from app.api.auth import account_deletion as mod

        mock_user = types.SimpleNamespace(
            id="test-id",
            email="test@example.com",
            is_deleted=False,
        )

        async def mock_get_user_by_id(db, user_id):
            return mock_user

        async def mock_confirm_deletion(db, user_id):
            return True

        async def mock_log_deletion(db, request, user, deletion_stage):
            pass  # Mock audit logging

        mock_email_service = MockEmailService(configured=True)
        mock_email_service.verify_deletion_token = AsyncMock(return_value="user-id")

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(mod, "email_service", mock_email_service)
            mp.setattr(mod.crud_user, "get_user_by_id", mock_get_user_by_id)
            mp.setattr(mod.crud_user, "confirm_account_deletion", mock_confirm_deletion)
            mp.setattr(mod, "log_account_deletion", mock_log_deletion)
            # Mock settings for grace period
            mp.setattr(mod.settings, "ACCOUNT_DELETION_GRACE_PERIOD_DAYS", 7)

            resp = await async_client.post(
                "/api/auth/confirm-deletion",
                json={"token": "valid-token"},
            )

            assert resp.status_code == 200
            data = resp.json()
            assert "Account deletion confirmed" in data["message"]
            assert data["deletion_confirmed"] is True
            assert "deletion_scheduled_for" in data
            # Should be 7 days from now
            scheduled_date = datetime.fromisoformat(
                data["deletion_scheduled_for"].replace("Z", "+00:00"),
            )
            expected_date = datetime.now(timezone.utc) + timedelta(days=7)
            time_diff = abs((scheduled_date - expected_date).total_seconds())
            assert time_diff < 60  # Within 1 minute

    async def test_confirm_deletion_unexpected_error(self, async_client):
        """Test deletion confirmation with unexpected error."""
        from app.api.auth import account_deletion as mod

        async def error_function(*args, **kwargs):
            raise Exception("Unexpected error during deletion confirmation")

        mock_email_service = MockEmailService(configured=True)
        mock_email_service.verify_deletion_token = error_function

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(mod, "email_service", mock_email_service)

            resp = await async_client.post(
                "/api/auth/confirm-deletion",
                json={"token": "valid-token"},
            )

            assert resp.status_code == 200
            data = resp.json()
            assert "deletion confirmation failed" in data["message"].lower()
            assert data["deletion_confirmed"] is False
