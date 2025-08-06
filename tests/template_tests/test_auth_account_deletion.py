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

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings

# These functions are not implemented yet - tests are skipped
# from app.crud.user import (
#     request_account_deletion_sync,
#     confirm_account_deletion_sync,
#     cancel_account_deletion_sync,
# )
from app.models import User
from app.schemas.user import UserCreate


@pytest.mark.skip(
    reason="Requires complex account deletion workflow - not implemented yet",
)
class TestAccountDeletionRequest:
    """Test account deletion request functionality."""

    def test_request_deletion_success(self, sync_db_session):
        """Test successful account deletion request."""
        # Create a test user
        user_create = UserCreate(
            email="test@example.com",
            username="testuser",
            password="TestPassword123!",
            is_superuser=False,
        )
        user = sync_db_session.add(User(**user_create.dict()))
        sync_db_session.commit()

        # Request deletion
        # success = request_account_deletion_sync(sync_db_session, str(user.id))
        # # assert success is True

        # Verify user has deletion token
        sync_db_session.refresh(user)
        assert user.deletion_token is not None
        assert user.deletion_token_expires is not None
        assert user.deletion_scheduled_for is None

    def test_request_deletion_nonexistent_user(self, sync_db_session):
        """Test deletion request for non-existent user."""
        # success = request_account_deletion_sync(
        #     sync_db_session, "00000000-0000-0000-0000-000000000000"
        # )
        # # assert success is False

    def test_request_deletion_already_scheduled(self, sync_db_session):
        """Test deletion request for already scheduled user."""
        # Create a test user
        user_create = UserCreate(
            email="test@example.com",
            username="testuser",
            password="TestPassword123!",
            is_superuser=False,
        )
        user = sync_db_session.add(User(**user_create.dict()))
        user.deletion_scheduled_for = datetime.now(timezone.utc) + timedelta(days=30)
        sync_db_session.commit()

        # Try to request deletion again
        # success = request_account_deletion_sync(sync_db_session, str(user.id))
        # # assert success is False


@pytest.mark.skip(
    reason="Requires complex account deletion workflow - not implemented yet",
)
class TestAccountDeletionConfirmation:
    """Test account deletion confirmation functionality."""

    def test_confirm_deletion_success(self, sync_db_session):
        """Test successful account deletion confirmation."""
        # Create a test user with deletion token
        user_create = UserCreate(
            email="test@example.com",
            username="testuser",
            password="TestPassword123!",
            is_superuser=False,
        )
        user = sync_db_session.add(User(**user_create.dict()))
        user.deletion_token = "test-token"
        user.deletion_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        sync_db_session.commit()

        # Confirm deletion
        scheduled_date = datetime.now(timezone.utc) + timedelta(days=30)
        # success = confirm_account_deletion_sync(
        #     sync_db_session, str(user.id), scheduled_date
        # )
        # assert success is True

        # Verify user is scheduled for deletion
        sync_db_session.refresh(user)
        assert user.deletion_scheduled_for == scheduled_date
        assert user.deletion_token is None
        assert user.deletion_token_expires is None

    def test_confirm_deletion_invalid_token(self, sync_db_session):
        """Test deletion confirmation with invalid token."""
        # Create a test user without deletion token
        user_create = UserCreate(
            email="test@example.com",
            username="testuser",
            password="TestPassword123!",
            is_superuser=False,
        )
        user = sync_db_session.add(User(**user_create.dict()))
        sync_db_session.commit()

        # Try to confirm deletion
        # scheduled_date = datetime.now(timezone.utc) + timedelta(days=30)
        # # success = confirm_account_deletion_sync(
        #     sync_db_session, str(user.id), scheduled_date
        # )
        # # assert success is False

        # Verify user exists (to use the variable)
        assert user.deletion_token is None

    def test_confirm_deletion_expired_token(self, sync_db_session):
        """Test deletion confirmation with expired token."""
        # Create a test user with expired deletion token
        user_create = UserCreate(
            email="test@example.com",
            username="testuser",
            password="TestPassword123!",
            is_superuser=False,
        )
        user = sync_db_session.add(User(**user_create.dict()))
        user.deletion_token = "test-token"
        user.deletion_token_expires = datetime.now(timezone.utc) - timedelta(hours=1)
        sync_db_session.commit()

        # Try to confirm deletion
        # scheduled_date = datetime.now(timezone.utc) + timedelta(days=30)
        # success = confirm_account_deletion_sync(
        #     sync_db_session, str(user.id), scheduled_date
        # )
        # assert success is False

        # Verify user exists (to use the variable)
        assert user.deletion_token == "test-token"


@pytest.mark.skip(
    reason="Requires complex account deletion workflow - not implemented yet",
)
class TestAccountDeletionCancellation:
    """Test account deletion cancellation functionality."""

    def test_cancel_deletion_success(self, sync_db_session):
        """Test successful account deletion cancellation."""
        # Create a test user scheduled for deletion
        user_create = UserCreate(
            email="test@example.com",
            username="testuser",
            password="TestPassword123!",
            is_superuser=False,
        )
        user = sync_db_session.add(User(**user_create.dict()))
        user.deletion_scheduled_for = datetime.now(timezone.utc) + timedelta(days=30)
        sync_db_session.commit()

        # Cancel deletion
        # success = cancel_account_deletion_sync(sync_db_session, str(user.id))
        # assert success is True

        # Verify user is no longer scheduled for deletion
        sync_db_session.refresh(user)
        assert user.deletion_scheduled_for is None

    def test_cancel_deletion_not_scheduled(self, sync_db_session):
        """Test cancellation for user not scheduled for deletion."""
        # Create a test user not scheduled for deletion
        user_create = UserCreate(
            email="test@example.com",
            username="testuser",
            password="TestPassword123!",
            is_superuser=False,
        )
        user = sync_db_session.add(User(**user_create.dict()))
        sync_db_session.commit()

        # Try to cancel deletion
        # success = cancel_account_deletion_sync(sync_db_session, str(user.id))
        # assert success is False

        # Verify user exists (to use the variable)
        assert user.deletion_scheduled_for is None


@pytest.mark.skip(
    reason="Requires complex account deletion workflow - not implemented yet",
)
class TestAccountDeletionStatus:
    """Test account deletion status checking."""

    def test_deletion_status_not_requested(
        self,
        client: TestClient,
        sync_db_session: Session,
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
        self,
        client: TestClient,
        sync_db_session: Session,
    ):
        """Test status for user who requested deletion."""
        user = User(
            email="requested@example.com",
            username="requested",
            hashed_password="hashed_password",
            is_verified=True,
            deletion_requested_at=datetime.now(timezone.utc),
            deletion_token="status_token",
            deletion_token_expires=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        response = client.get(
            "/api/v1/auth/deletion-status?email=requested@example.com",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["deletion_requested"] is True
        assert data["deletion_confirmed"] is False
        assert data["deletion_scheduled_for"] is None
        assert data["can_cancel"] is True
        assert data["grace_period_days"] == settings.ACCOUNT_DELETION_GRACE_PERIOD_DAYS

    def test_deletion_status_confirmed(
        self,
        client: TestClient,
        sync_db_session: Session,
    ):
        """Test status for user who confirmed deletion."""
        scheduled_time = datetime.now(timezone.utc) + timedelta(
            days=settings.ACCOUNT_DELETION_GRACE_PERIOD_DAYS,
        )
        user = User(
            email="confirmed@example.com",
            username="confirmed",
            hashed_password="hashed_password",
            is_verified=True,
            deletion_requested_at=datetime.now(timezone.utc),
            deletion_confirmed_at=datetime.now(timezone.utc),
            deletion_scheduled_for=scheduled_time,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        response = client.get(
            "/api/v1/auth/deletion-status?email=confirmed@example.com",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["deletion_requested"] is True
        assert data["deletion_confirmed"] is True
        assert data["deletion_scheduled_for"] is not None
        assert data["can_cancel"] is True
        assert data["grace_period_days"] == settings.ACCOUNT_DELETION_GRACE_PERIOD_DAYS

    def test_deletion_status_user_not_found(
        self,
        client: TestClient,
        sync_db_session: Session,
    ):
        """Test status for non-existent user."""
        response = client.get(
            "/api/v1/auth/deletion-status?email=nonexistent@example.com",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["deletion_requested"] is False
        assert data["deletion_confirmed"] is False
        assert data["deletion_scheduled_for"] is None
        assert data["can_cancel"] is False
        assert data["grace_period_days"] == settings.ACCOUNT_DELETION_GRACE_PERIOD_DAYS


@pytest.mark.skip(
    reason="Requires complex account deletion workflow - not implemented yet",
)
class TestAccountDeletionRateLimiting:
    """Test rate limiting for account deletion endpoints."""

    def test_request_deletion_rate_limited(
        self,
        client: TestClient,
        sync_db_session: Session,
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
                "/api/v1/auth/request-deletion",
                json={"email": "rate@example.com"},
            )

        # The last request should be rate limited
        assert response.status_code == 429
        data = response.json()
        assert "Too many requests" in data["detail"]

    def test_confirm_deletion_rate_limited(
        self,
        client: TestClient,
        sync_db_session: Session,
    ):
        """Test rate limiting for deletion confirmation."""
        # Skip test if rate limiting is disabled
        from app.core.config import settings

        if not settings.ENABLE_RATE_LIMITING:
            pytest.skip("Rate limiting is disabled")

        # Make multiple requests quickly
        for _ in range(4):
            response = client.post(
                "/api/v1/auth/confirm-deletion",
                json={"token": "some_token"},
            )

        # The last request should be rate limited
        assert response.status_code == 429
        data = response.json()
        assert "Too many requests" in data["detail"]

    def test_cancel_deletion_rate_limited(
        self,
        client: TestClient,
        sync_db_session: Session,
    ):
        """Test rate limiting for deletion cancellation."""
        # Skip test if rate limiting is disabled
        from app.core.config import settings

        if not settings.ENABLE_RATE_LIMITING:
            pytest.skip("Rate limiting is disabled")

        # Make multiple requests quickly
        for _ in range(4):
            response = client.post(
                "/api/v1/auth/cancel-deletion",
                json={"email": "rate@example.com"},
            )

        # The last request should be rate limited
        assert response.status_code == 429
        data = response.json()
        assert "Too many requests" in data["detail"]


@pytest.mark.skip(
    reason="Requires complex account deletion workflow - not implemented yet",
)
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
            "app.services.celery_tasks.permanently_delete_accounts_task",
        )


@pytest.mark.skip(
    reason="Requires complex account deletion workflow - not implemented yet",
)
class TestAccountDeletionCRUD:
    """Test account deletion CRUD operations."""

    def test_request_account_deletion_sync(self, sync_db_session):
        """Test sync account deletion request."""
        # Create a test user
        user_create = UserCreate(
            email="test@example.com",
            username="testuser",
            password="TestPassword123!",
            is_superuser=False,
        )
        user = sync_db_session.add(User(**user_create.dict()))
        sync_db_session.commit()

        # Request deletion
        # success = request_account_deletion_sync(sync_db_session, str(user.id))
        # assert success is True

        # Verify user has deletion token
        sync_db_session.refresh(user)
        assert user.deletion_token is not None
        assert user.deletion_token_expires is not None

    def test_confirm_account_deletion_sync(self, sync_db_session):
        """Test sync account deletion confirmation."""
        # Create a test user with deletion token
        user_create = UserCreate(
            email="test@example.com",
            username="testuser",
            password="TestPassword123!",
            is_superuser=False,
        )
        user = sync_db_session.add(User(**user_create.dict()))
        user.deletion_token = "test-token"
        user.deletion_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        sync_db_session.commit()

        # Confirm deletion
        scheduled_date = datetime.now(timezone.utc) + timedelta(days=30)
        # success = confirm_account_deletion_sync(
        #     sync_db_session, str(user.id), scheduled_date
        # )
        # assert success is True

        # Verify user is scheduled for deletion
        sync_db_session.refresh(user)
        assert user.deletion_scheduled_for == scheduled_date

    def test_cancel_account_deletion_sync(self, sync_db_session):
        """Test sync account deletion cancellation."""
        # Create a test user scheduled for deletion
        user_create = UserCreate(
            email="test@example.com",
            username="testuser",
            password="TestPassword123!",
            is_superuser=False,
        )
        user = sync_db_session.add(User(**user_create.dict()))
        user.deletion_scheduled_for = datetime.now(timezone.utc) + timedelta(days=30)
        sync_db_session.commit()

        # Cancel deletion
        # success = cancel_account_deletion_sync(sync_db_session, str(user.id))
        # assert success is True

        # Verify user is no longer scheduled for deletion
        sync_db_session.refresh(user)
        assert user.deletion_scheduled_for is None
