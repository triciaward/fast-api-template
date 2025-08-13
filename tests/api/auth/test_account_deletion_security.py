"""Account deletion security tests."""

import types
from unittest.mock import AsyncMock

import pytest

from tests.utils.auth_helpers import MockEmailService

pytestmark = pytest.mark.asyncio


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
                "/api/auth/request-deletion",
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
                    "/api/auth/request-deletion",
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
                "/api/auth/confirm-deletion",
                json={"token": ""},
            )
            assert (
                resp.status_code == 200
            )  # Application handles empty tokens gracefully

            # Test malformed token
            resp = await async_client.post(
                "/api/auth/confirm-deletion",
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
                "/api/auth/request-deletion",
                json={"email": "test@example.com"},
            )

            assert resp.status_code == 200
            assert "deletion_requested" in audit_logs
