"""
Tests for account deletion functionality.

This module tests the complete account deletion workflow including:
- Requesting account deletion
- Confirming account deletion with token
- Canceling account deletion
- Checking deletion status
- Rate limiting
- Email notifications
- Background task processing
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import User


class TestAccountDeletionRequest:
    """Test account deletion request functionality."""

    def test_request_deletion_success(
        self, client: TestClient, sync_db_session: Session
    ):
        """Test successful account deletion request."""
        # Create a test user
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()
        sync_db_session.refresh(user)

        with patch(
            "app.services.email.EmailService.is_configured"
        ) as mock_configured, patch(
            "app.services.email.EmailService.send_account_deletion_email"
        ) as mock_send_email:
            mock_configured.return_value = True
            mock_send_email.return_value = True

            response = client.post(
                "/api/v1/auth/request-deletion", json={"email": "test@example.com"}
            )

        assert response.status_code == 200
        data = response.json()
        assert (
            data["message"]
            == "If an account with that email exists, a deletion confirmation link has been sent."
        )
        assert data["email_sent"] is True

        # Verify user state
        sync_db_session.refresh(user)
        assert user.deletion_requested_at is not None
        assert user.deletion_token is not None
        assert user.deletion_token_expires is not None
        assert user.is_deleted is False

    def test_request_deletion_user_not_found(
        self, client: TestClient, sync_db_session: Session
    ):
        """Test deletion request for non-existent user."""
        response = client.post(
            "/api/v1/auth/request-deletion", json={"email": "nonexistent@example.com"}
        )

        assert response.status_code == 200
        data = response.json()
        assert (
            data["message"]
            == "If an account with that email exists, a deletion confirmation link has been sent."
        )
        assert data["email_sent"] is True

    def test_request_deletion_already_requested(
        self, client: TestClient, sync_db_session: Session
    ):
        """Test deletion request for user who already requested deletion."""
        user = User(
            email="already@example.com",
            username="already",
            hashed_password="hashed_password",
            is_verified=True,
            deletion_requested_at=datetime.utcnow(),
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        response = client.post(
            "/api/v1/auth/request-deletion", json={"email": "already@example.com"}
        )

        assert response.status_code == 200
        data = response.json()
        assert (
            data["message"]
            == "If an account with that email exists, a deletion confirmation link has been sent."
        )
        assert data["email_sent"] is True

    def test_request_deletion_email_not_configured(
        self, client: TestClient, sync_db_session: Session
    ):
        """Test deletion request when email service is not configured."""
        user = User(
            email="noconfig@example.com",
            username="noconfig",
            hashed_password="hashed_password",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        with patch("app.services.email.EmailService.is_configured") as mock_configured:
            mock_configured.return_value = False

            response = client.post(
                "/api/v1/auth/request-deletion", json={"email": "noconfig@example.com"}
            )

        assert response.status_code == 200
        data = response.json()
        assert (
            data["message"]
            == "Account deletion service temporarily unavailable. Please try again later."
        )
        assert data["email_sent"] is False


class TestAccountDeletionConfirmation:
    """Test account deletion confirmation functionality."""

    def test_confirm_deletion_success(
        self, client: TestClient, sync_db_session: Session
    ):
        """Test successful account deletion confirmation."""
        # Create user with deletion request
        user = User(
            email="confirm@example.com",
            username="confirm",
            hashed_password="hashed_password",
            is_verified=True,
            deletion_requested_at=datetime.utcnow(),
            deletion_token="valid_token_123",
            deletion_token_expires=datetime.utcnow() + timedelta(hours=1),
        )
        sync_db_session.add(user)
        sync_db_session.commit()
        sync_db_session.refresh(user)

        with patch(
            "app.services.email.EmailService.is_configured"
        ) as mock_configured, patch(
            "app.services.email.EmailService.verify_deletion_token"
        ) as mock_verify:
            mock_configured.return_value = True
            mock_verify.return_value = str(user.id)

            response = client.post(
                "/api/v1/auth/confirm-deletion", json={"token": "valid_token_123"}
            )

        assert response.status_code == 200
        data = response.json()
        assert "Account deletion confirmed" in data["message"]
        assert data["deletion_confirmed"] is True
        assert data["deletion_scheduled_for"] is not None

        # Verify user state
        sync_db_session.refresh(user)
        assert user.deletion_confirmed_at is not None
        assert user.deletion_scheduled_for is not None
        assert user.is_deleted is False

    def test_confirm_deletion_invalid_token(
        self, client: TestClient, sync_db_session: Session
    ):
        """Test confirmation with invalid token."""
        with patch(
            "app.services.email.EmailService.is_configured"
        ) as mock_configured, patch(
            "app.services.email.EmailService.verify_deletion_token"
        ) as mock_verify:
            mock_configured.return_value = True
            mock_verify.return_value = None

            response = client.post(
                "/api/v1/auth/confirm-deletion", json={"token": "invalid_token"}
            )

        assert response.status_code == 200
        data = response.json()
        assert (
            data["message"]
            == "Invalid or expired deletion token. Please request a new one."
        )
        assert data["deletion_confirmed"] is False

    def test_confirm_deletion_email_not_configured(
        self, client: TestClient, sync_db_session: Session
    ):
        """Test confirmation when email service is not configured."""
        with patch("app.services.email.EmailService.is_configured") as mock_configured:
            mock_configured.return_value = False

            response = client.post(
                "/api/v1/auth/confirm-deletion", json={"token": "some_token"}
            )

        assert response.status_code == 200
        data = response.json()
        assert (
            data["message"]
            == "Account deletion service temporarily unavailable. Please try again later."
        )
        assert data["deletion_confirmed"] is False


class TestAccountDeletionCancellation:
    """Test account deletion cancellation functionality."""

    def test_cancel_deletion_success(
        self, client: TestClient, sync_db_session: Session
    ):
        """Test successful account deletion cancellation."""
        user = User(
            email="cancel@example.com",
            username="cancel",
            hashed_password="hashed_password",
            is_verified=True,
            deletion_requested_at=datetime.utcnow(),
            deletion_token="cancel_token",
            deletion_token_expires=datetime.utcnow() + timedelta(hours=1),
        )
        sync_db_session.add(user)
        sync_db_session.commit()
        sync_db_session.refresh(user)

        response = client.post(
            "/api/v1/auth/cancel-deletion", json={"email": "cancel@example.com"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "Account deletion" in data["message"] and "cancelled" in data["message"]
        assert data["deletion_cancelled"] is True

        # Verify user state is reset
        sync_db_session.refresh(user)
        assert user.deletion_requested_at is None
        assert user.deletion_confirmed_at is None
        assert user.deletion_scheduled_for is None
        assert user.deletion_token is None
        assert user.deletion_token_expires is None
        assert user.is_deleted is False

    def test_cancel_deletion_user_not_found(
        self, client: TestClient, sync_db_session: Session
    ):
        """Test cancellation for non-existent user."""
        response = client.post(
            "/api/v1/auth/cancel-deletion", json={"email": "nonexistent@example.com"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "cancelled" in data["message"]
        assert data["deletion_cancelled"] is True

    def test_cancel_deletion_no_request(
        self, client: TestClient, sync_db_session: Session
    ):
        """Test cancellation when no deletion was requested."""
        user = User(
            email="norequest@example.com",
            username="norequest",
            hashed_password="hashed_password",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        response = client.post(
            "/api/v1/auth/cancel-deletion", json={"email": "norequest@example.com"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "cancelled" in data["message"]
        assert data["deletion_cancelled"] is True


class TestAccountDeletionStatus:
    """Test account deletion status checking."""

    def test_deletion_status_not_requested(
        self, client: TestClient, sync_db_session: Session
    ):
        """Test status for user who hasn't requested deletion."""
        user = User(
            email="status@example.com",
            username="status",
            hashed_password="hashed_password",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        response = client.get("/api/v1/auth/deletion-status?email=status@example.com")

        assert response.status_code == 200
        data = response.json()
        assert data["deletion_requested"] is False
        assert data["deletion_confirmed"] is False
        assert data["deletion_scheduled_for"] is None
        assert data["can_cancel"] is False
        assert data["grace_period_days"] == settings.ACCOUNT_DELETION_GRACE_PERIOD_DAYS

    def test_deletion_status_requested(
        self, client: TestClient, sync_db_session: Session
    ):
        """Test status for user who requested deletion."""
        user = User(
            email="requested@example.com",
            username="requested",
            hashed_password="hashed_password",
            is_verified=True,
            deletion_requested_at=datetime.utcnow(),
            deletion_token="status_token",
            deletion_token_expires=datetime.utcnow() + timedelta(hours=1),
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        response = client.get(
            "/api/v1/auth/deletion-status?email=requested@example.com"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["deletion_requested"] is True
        assert data["deletion_confirmed"] is False
        assert data["deletion_scheduled_for"] is None
        assert data["can_cancel"] is True
        assert data["grace_period_days"] == settings.ACCOUNT_DELETION_GRACE_PERIOD_DAYS

    def test_deletion_status_confirmed(
        self, client: TestClient, sync_db_session: Session
    ):
        """Test status for user who confirmed deletion."""
        scheduled_time = datetime.utcnow() + timedelta(
            days=settings.ACCOUNT_DELETION_GRACE_PERIOD_DAYS
        )
        user = User(
            email="confirmed@example.com",
            username="confirmed",
            hashed_password="hashed_password",
            is_verified=True,
            deletion_requested_at=datetime.utcnow(),
            deletion_confirmed_at=datetime.utcnow(),
            deletion_scheduled_for=scheduled_time,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        response = client.get(
            "/api/v1/auth/deletion-status?email=confirmed@example.com"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["deletion_requested"] is True
        assert data["deletion_confirmed"] is True
        assert data["deletion_scheduled_for"] is not None
        assert data["can_cancel"] is True
        assert data["grace_period_days"] == settings.ACCOUNT_DELETION_GRACE_PERIOD_DAYS

    def test_deletion_status_user_not_found(
        self, client: TestClient, sync_db_session: Session
    ):
        """Test status for non-existent user."""
        response = client.get(
            "/api/v1/auth/deletion-status?email=nonexistent@example.com"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["deletion_requested"] is False
        assert data["deletion_confirmed"] is False
        assert data["deletion_scheduled_for"] is None
        assert data["can_cancel"] is False
        assert data["grace_period_days"] == settings.ACCOUNT_DELETION_GRACE_PERIOD_DAYS


class TestAccountDeletionRateLimiting:
    """Test rate limiting for account deletion endpoints."""

    def test_request_deletion_rate_limited(
        self, client: TestClient, sync_db_session: Session
    ):
        """Test rate limiting for deletion requests."""
        # Skip test if rate limiting is disabled
        from app.core.config import settings

        if not settings.ENABLE_RATE_LIMITING:
            pytest.skip("Rate limiting is disabled")

        user = User(
            email="rate@example.com",
            username="rate",
            hashed_password="hashed_password",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        # Make multiple requests quickly
        for _ in range(4):
            response = client.post(
                "/api/v1/auth/request-deletion", json={"email": "rate@example.com"}
            )

        # The last request should be rate limited
        assert response.status_code == 429
        data = response.json()
        assert "Too many requests" in data["detail"]

    def test_confirm_deletion_rate_limited(
        self, client: TestClient, sync_db_session: Session
    ):
        """Test rate limiting for deletion confirmation."""
        # Skip test if rate limiting is disabled
        from app.core.config import settings

        if not settings.ENABLE_RATE_LIMITING:
            pytest.skip("Rate limiting is disabled")

        # Make multiple requests quickly
        for _ in range(4):
            response = client.post(
                "/api/v1/auth/confirm-deletion", json={"token": "some_token"}
            )

        # The last request should be rate limited
        assert response.status_code == 429
        data = response.json()
        assert "Too many requests" in data["detail"]

    def test_cancel_deletion_rate_limited(
        self, client: TestClient, sync_db_session: Session
    ):
        """Test rate limiting for deletion cancellation."""
        # Skip test if rate limiting is disabled
        from app.core.config import settings

        if not settings.ENABLE_RATE_LIMITING:
            pytest.skip("Rate limiting is disabled")

        # Make multiple requests quickly
        for _ in range(4):
            response = client.post(
                "/api/v1/auth/cancel-deletion", json={"email": "rate@example.com"}
            )

        # The last request should be rate limited
        assert response.status_code == 429
        data = response.json()
        assert "Too many requests" in data["detail"]


@pytest.mark.celery
class TestAccountDeletionCeleryTask:
    """Test the background task for permanent account deletion."""

    def test_permanently_delete_accounts_task_endpoint(self, client: TestClient):
        """Test the manual trigger endpoint for the deletion task."""
        # Skip test if Celery is disabled
        from app.core.config import settings

        if not settings.ENABLE_CELERY:
            pytest.skip("Celery is disabled")

        with patch("app.api.api_v1.endpoints.celery.submit_task") as mock_submit_task:
            mock_result = MagicMock()
            mock_result.id = "task_123"
            mock_submit_task.return_value = mock_result

            response = client.post("/api/v1/celery/tasks/permanently-delete-accounts")

        assert response.status_code == 200
        data = response.json()
        assert (
            data["message"] == "Permanent account deletion task submitted successfully"
        )
        assert data["task_id"] == "task_123"
        mock_submit_task.assert_called_once_with(
            "app.services.celery_tasks.permanently_delete_accounts_task"
        )


class TestAccountDeletionCRUD:
    """Test CRUD operations for account deletion."""

    def test_request_account_deletion_sync(self, sync_db_session: Session):
        """Test requesting account deletion via CRUD."""
        from app.crud.user import request_account_deletion_sync

        user = User(
            email="crud@example.com",
            username="crud",
            hashed_password="hashed_password",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        result = request_account_deletion_sync(sync_db_session, str(user.id))

        assert result is True
        sync_db_session.refresh(user)
        assert user.deletion_requested_at is not None

    def test_confirm_account_deletion_sync(self, sync_db_session: Session):
        """Test confirming account deletion via CRUD."""
        from app.crud.user import (
            confirm_account_deletion_sync,
            request_account_deletion_sync,
        )

        user = User(
            email="confirm_crud@example.com",
            username="confirm_crud",
            hashed_password="hashed_password",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        # First request deletion
        request_account_deletion_sync(sync_db_session, str(user.id))

        # Then confirm deletion
        scheduled_time = datetime.utcnow() + timedelta(
            days=settings.ACCOUNT_DELETION_GRACE_PERIOD_DAYS
        )
        result = confirm_account_deletion_sync(
            sync_db_session, str(user.id), scheduled_time
        )

        assert result is True
        sync_db_session.refresh(user)
        assert user.deletion_confirmed_at is not None
        assert user.deletion_scheduled_for is not None

    def test_cancel_account_deletion_sync(self, sync_db_session: Session):
        """Test canceling account deletion via CRUD."""
        from app.crud.user import (
            cancel_account_deletion_sync,
            request_account_deletion_sync,
        )

        user = User(
            email="cancel_crud@example.com",
            username="cancel_crud",
            hashed_password="hashed_password",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        # First request deletion
        request_account_deletion_sync(sync_db_session, str(user.id))

        # Then cancel deletion
        result = cancel_account_deletion_sync(sync_db_session, str(user.id))

        assert result is True
        sync_db_session.refresh(user)
        assert user.deletion_requested_at is None
        assert user.deletion_token is None
        assert user.deletion_token_expires is None
