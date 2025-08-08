"""Comprehensive account deletion edge case tests to improve coverage."""

import types
from datetime import datetime, timedelta, timezone
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
                "/auth/request-deletion",
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
                "/auth/request-deletion",
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
                "/auth/request-deletion",
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
                "/auth/request-deletion",
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
                "/auth/request-deletion",
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
                "/auth/request-deletion",
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
                "/auth/request-deletion",
                json={"email": "test@example.com"},
            )

            assert resp.status_code == 200
            data = resp.json()
            assert "deletion request failed" in data["message"].lower()
            assert data["email_sent"] is False


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
                "/auth/confirm-deletion",
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
                "/auth/confirm-deletion",
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
                "/auth/confirm-deletion",
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
                "/auth/confirm-deletion",
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
                "/auth/confirm-deletion",
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
                "/auth/confirm-deletion",
                json={"token": "valid-token"},
            )

            assert resp.status_code == 200
            data = resp.json()
            assert "Account deletion confirmed" in data["message"]
            assert data["deletion_confirmed"] is True
            assert "deletion_scheduled_for" in data
            # Should be 7 days from now
            scheduled_date = datetime.fromisoformat(
                data["deletion_scheduled_for"].replace("Z", "+00:00")
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
                "/auth/confirm-deletion",
                json={"token": "valid-token"},
            )

            assert resp.status_code == 200
            data = resp.json()
            assert "deletion confirmation failed" in data["message"].lower()
            assert data["deletion_confirmed"] is False


class TestAccountDeletionSecurityScenarios:
    """Test security-related scenarios for account deletion."""

    async def test_deletion_request_for_nonexistent_user(self, async_client):
        """Test deletion request for non-existent user doesn't reveal user existence."""
        from app.api.auth import account_deletion as mod

        async def mock_get_user(db, email):
            return None  # User doesn't exist

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(mod.crud_user, "get_user_by_email", mock_get_user)

            resp = await async_client.post(
                "/auth/request-deletion",
                json={"email": "nonexistent@example.com"},
            )

            assert resp.status_code == 200
            data = resp.json()
            # Should not reveal that user doesn't exist
            assert "If an account with that email exists" in data["message"]
            assert data["email_sent"] is True

    async def test_deletion_request_rate_limiting_integration(self, async_client):
        """Test deletion request with rate limiting."""
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
            pass

        mock_email_service = MockEmailService(configured=True)
        mock_email_service.create_deletion_token = AsyncMock(return_value="token123")
        mock_email_service.send_account_deletion_email = lambda *args: True

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(mod.crud_user, "get_user_by_email", mock_get_user)
            mp.setattr(mod.crud_user, "request_account_deletion", mock_request_deletion)
            mp.setattr(mod, "email_service", mock_email_service)
            mp.setattr(mod, "log_account_deletion", mock_log_deletion)

            # Multiple requests should still work (rate limiting is handled by decorator)
            for _ in range(3):
                resp = await async_client.post(
                    "/auth/request-deletion",
                    json={"email": "test@example.com"},
                )
                assert resp.status_code == 200

    async def test_deletion_token_tampering_scenarios(self, async_client):
        """Test various token tampering scenarios."""
        from app.api.auth import account_deletion as mod

        mock_email_service = MockEmailService(configured=True)

        # Test empty token
        mock_email_service.verify_deletion_token = AsyncMock(return_value=None)

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(mod, "email_service", mock_email_service)

            resp = await async_client.post(
                "/auth/confirm-deletion",
                json={"token": ""},
            )
            assert (
                resp.status_code == 200
            )  # Application handles empty tokens gracefully

            # Test malformed token
            resp = await async_client.post(
                "/auth/confirm-deletion",
                json={"token": "malformed.token.here"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "Invalid or expired deletion token" in data["message"]

    async def test_deletion_audit_logging_scenarios(self, async_client):
        """Test audit logging for deletion scenarios."""
        from app.api.auth import account_deletion as mod

        mock_user = types.SimpleNamespace(
            id="test-id",
            email="test@example.com",
            username="testuser",
            is_deleted=False,
            deletion_requested_at=None,
        )

        audit_logs = []

        async def mock_get_user(db, email):
            return mock_user

        async def mock_request_deletion(db, user_id):
            return True

        async def mock_log_deletion(db, request, user, deletion_stage):
            audit_logs.append(deletion_stage)

        mock_email_service = MockEmailService(configured=True)
        mock_email_service.create_deletion_token = AsyncMock(return_value="token123")
        mock_email_service.send_account_deletion_email = lambda *args: True

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(mod.crud_user, "get_user_by_email", mock_get_user)
            mp.setattr(mod.crud_user, "request_account_deletion", mock_request_deletion)
            mp.setattr(mod, "email_service", mock_email_service)
            mp.setattr(mod, "log_account_deletion", mock_log_deletion)

            resp = await async_client.post(
                "/auth/request-deletion",
                json={"email": "test@example.com"},
            )

            assert resp.status_code == 200
            assert "deletion_requested" in audit_logs
