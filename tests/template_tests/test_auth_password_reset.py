import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.fixture(autouse=True)
def always_configured_email(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch email service to always be configured for all tests in this file."""
    monkeypatch.setattr("app.services.email.email_service.is_configured", lambda: True)


@pytest.mark.skip(
    reason="Requires complex password reset workflow - not implemented yet"
)
class TestPasswordResetEndpoints:
    def test_forgot_password_success(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test successful password reset request."""
        # Create user
        from app.core.security import get_password_hash
        from app.models import User

        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("OldPassword123!"),
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        with patch(
            "app.services.email.email_service.send_password_reset_email",
            return_value=True,
        ):
            response = client.post(
                "/api/v1/auth/forgot-password", json={"email": "test@example.com"}
            )
            assert response.status_code == 200
            data = response.json()
            assert (
                data["message"]
                == "If an account with that email exists, a password reset link has been sent."
            )
            assert data["email_sent"] is True

    def test_forgot_password_user_not_found(self, client: TestClient) -> None:
        """Test password reset request for non-existent user."""
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nonexistent@example.com"},
        )
        assert response.status_code == 200
        data = response.json()
        assert (
            data["message"]
            == "If an account with that email exists, a password reset link has been sent."
        )
        assert data["email_sent"] is True

    def test_forgot_password_oauth_user(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test password reset request for OAuth user (should be blocked)."""
        # Create OAuth user
        from app.models import User

        user = User(
            email="oauth@example.com",
            username="oauthuser",
            hashed_password=None,  # OAuth users don't have passwords
            is_verified=True,
            oauth_provider="google",
            oauth_id="google_123",
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        response = client.post(
            "/api/v1/auth/forgot-password", json={"email": "oauth@example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert (
            data["message"]
            == "If an account with that email exists, a password reset link has been sent."
        )
        assert data["email_sent"] is True

    def test_forgot_password_email_not_configured(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test password reset request when email is not configured."""
        # Create user
        from app.core.security import get_password_hash
        from app.models import User

        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("OldPassword123!"),
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        with patch(
            "app.services.email.email_service.is_configured", return_value=False
        ):
            response = client.post(
                "/api/v1/auth/forgot-password", json={"email": "test@example.com"}
            )
            assert response.status_code == 200
            data = response.json()
            assert (
                data["message"]
                == "Password reset service temporarily unavailable. Please try again later."
            )
            assert data["email_sent"] is False

    def test_forgot_password_token_creation_failed(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test password reset request when token creation fails."""
        # Create user
        from app.core.security import get_password_hash
        from app.models import User

        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("OldPassword123!"),
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        with patch(
            "app.services.email.email_service.create_password_reset_token",
            return_value=None,
        ):
            response = client.post(
                "/api/v1/auth/forgot-password", json={"email": "test@example.com"}
            )
            assert response.status_code == 200
            data = response.json()
            assert (
                data["message"]
                == "Failed to create password reset token. Please try again later."
            )
            assert data["email_sent"] is False

    def test_forgot_password_email_send_failed(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test password reset request when email sending fails."""
        # Create user
        from app.core.security import get_password_hash
        from app.models import User

        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("OldPassword123!"),
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        with patch(
            "app.services.email.email_service.send_password_reset_email",
            return_value=False,
        ):
            response = client.post(
                "/api/v1/auth/forgot-password", json={"email": "test@example.com"}
            )
            assert response.status_code == 200
            data = response.json()
            assert (
                data["message"]
                == "Failed to send password reset email. Please try again later."
            )
            assert data["email_sent"] is False

    def test_reset_password_success(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test successful password reset."""
        # Create user with password reset token
        from app.core.security import get_password_hash
        from app.models import User

        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("OldPassword123!"),
            is_verified=True,
            password_reset_token="valid_reset_token",
            password_reset_token_expires=datetime.now(timezone.utc)
            + timedelta(hours=1),
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        response = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "valid_reset_token",
                "new_password": "NewPassword123!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert (
            data["message"]
            == "Password reset successfully. You can now log in with your new password."
        )
        assert data["password_reset"] is True

        # Verify password was actually changed by refreshing from database
        sync_db_session.refresh(user)

        # Test password verification directly
        from app.core.security import verify_password

        assert not verify_password("OldPassword123!", str(user.hashed_password))
        assert verify_password("NewPassword123!", str(user.hashed_password))

        # Verify reset token was cleared
        assert user.password_reset_token is None
        assert user.password_reset_token_expires is None

        # Verify authentication works with new password
        from app.crud.user import authenticate_user_sync

        # Old password should not work
        old_auth = authenticate_user_sync(
            sync_db_session, "test@example.com", "OldPassword123!"
        )
        assert old_auth is None

        # New password should work
        new_auth = authenticate_user_sync(
            sync_db_session, "test@example.com", "NewPassword123!"
        )
        assert new_auth is not None
        assert new_auth.email == "test@example.com"

    def test_reset_password_invalid_token(self, client: TestClient) -> None:
        """Test password reset with invalid token."""
        response = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "invalid_token",
                "new_password": "NewPassword123!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert (
            data["message"]
            == "Invalid or expired password reset token. Please request a new one."
        )
        assert data["password_reset"] is False

    def test_reset_password_expired_token(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test password reset with expired token."""
        # Create user with expired password reset token
        from app.core.security import get_password_hash
        from app.models import User

        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("OldPassword123!"),
            is_verified=True,
            password_reset_token="expired_reset_token",
            password_reset_token_expires=datetime.now(timezone.utc)
            - timedelta(hours=1),
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        response = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "expired_reset_token",
                "new_password": "NewPassword123!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert (
            data["message"]
            == "Invalid or expired password reset token. Please request a new one."
        )
        assert data["password_reset"] is False

    def test_reset_password_oauth_user(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test password reset for OAuth user (should be blocked)."""
        # Create OAuth user with password reset token
        from app.models import User

        user = User(
            email="oauth@example.com",
            username="oauthuser",
            hashed_password=None,
            is_verified=True,
            oauth_provider="google",
            oauth_id="google_123",
            password_reset_token="valid_reset_token",
            password_reset_token_expires=datetime.now(timezone.utc)
            + timedelta(hours=1),
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        response = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "valid_reset_token",
                "new_password": "NewPassword123!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert (
            data["message"]
            == "Invalid or expired password reset token. Please request a new one."
        )
        assert data["password_reset"] is False

    def test_reset_password_email_not_configured(self, client: TestClient) -> None:
        """Test password reset when email service is not configured."""
        with patch(
            "app.services.email.email_service.is_configured", return_value=False
        ):
            response = client.post(
                "/api/v1/auth/reset-password",
                json={
                    "token": "valid_token",
                    "new_password": "NewPassword123!",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert (
                data["message"]
                == "Password reset service temporarily unavailable. Please try again later."
            )
            assert data["password_reset"] is False

    def test_reset_password_user_not_found(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test password reset when user is not found."""
        # Create user with password reset token
        from app.core.security import get_password_hash
        from app.models import User

        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("OldPassword123!"),
            is_verified=True,
            password_reset_token="valid_reset_token",
            password_reset_token_expires=datetime.now(timezone.utc)
            + timedelta(hours=1),
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        # Delete the user to simulate user not found
        sync_db_session.delete(user)
        sync_db_session.commit()

        response = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "valid_reset_token",
                "new_password": "NewPassword123!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert (
            data["message"]
            == "Invalid or expired password reset token. Please request a new one."
        )
        assert data["password_reset"] is False

    def test_reset_password_weak_password(self, client: TestClient) -> None:
        """Test password reset with weak password."""
        response = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "valid_token",
                "new_password": "weak",
            },
        )
        assert response.status_code == 422  # Validation error
        error_data = response.json()
        assert "new_password" in str(error_data)

    def test_reset_password_invalid_email_format(self, client: TestClient) -> None:
        """Test forgot password with invalid email format."""
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "invalid-email"},
        )
        assert response.status_code == 422  # Validation error
        error_data = response.json()
        assert "email" in str(error_data)


@pytest.mark.skip(
    reason="Requires complex password reset workflow - not implemented yet"
)
class TestPasswordResetCRUDOperations:
    def test_get_user_by_password_reset_token_sync(
        self, sync_db_session: Session
    ) -> None:
        """Test getting user by password reset token."""
        from app.core.security import get_password_hash
        from app.crud.user import get_user_by_password_reset_token_sync
        from app.models import User

        # Create user with password reset token
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("TestPassword123!"),
            is_verified=True,
            password_reset_token="test_reset_token",
            password_reset_token_expires=datetime.now(timezone.utc)
            + timedelta(hours=1),
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        # Test finding user by token
        found_user = get_user_by_password_reset_token_sync(
            sync_db_session, "test_reset_token"
        )
        assert found_user is not None
        assert found_user.email == "test@example.com"
        assert found_user.password_reset_token == "test_reset_token"

        # Test with non-existent token
        not_found_user = get_user_by_password_reset_token_sync(
            sync_db_session, "non_existent_token"
        )
        assert not_found_user is None

    def test_update_password_reset_token_sync(self, sync_db_session: Session) -> None:
        """Test updating password reset token."""
        from app.core.security import get_password_hash
        from app.crud.user import update_password_reset_token_sync
        from app.models import User

        # Create user
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("TestPassword123!"),
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        user_id = str(user.id)
        token = "new_reset_token"
        expires = datetime.now(timezone.utc) + timedelta(hours=1)

        # Update password reset token
        success = update_password_reset_token_sync(
            sync_db_session, user_id, token, expires
        )
        assert success is True

        # Verify token was updated
        sync_db_session.refresh(user)
        assert user.password_reset_token == token
        assert user.password_reset_token_expires == expires

    def test_update_password_reset_token_user_not_found(
        self, sync_db_session: Session
    ) -> None:
        """Test updating password reset token for non-existent user."""
        from app.crud.user import update_password_reset_token_sync

        token = "new_reset_token"
        expires = datetime.now(timezone.utc) + timedelta(hours=1)

        # Try to update token for non-existent user with valid UUID format
        fake_uuid = str(uuid.uuid4())
        success = update_password_reset_token_sync(
            sync_db_session, fake_uuid, token, expires
        )
        assert success is False

    def test_reset_user_password_sync(self, sync_db_session: Session) -> None:
        """Test resetting user password."""
        from app.core.security import get_password_hash, verify_password
        from app.crud.user import reset_user_password_sync
        from app.models import User

        # Create user with password reset token
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("OldPassword123!"),
            is_verified=True,
            password_reset_token="test_reset_token",
            password_reset_token_expires=datetime.now(timezone.utc)
            + timedelta(hours=1),
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        user_id = str(user.id)
        new_password = "NewPassword123!"

        # Reset password
        success = reset_user_password_sync(sync_db_session, user_id, new_password)
        assert success is True

        # Verify password was changed
        sync_db_session.refresh(user)
        assert verify_password(new_password, str(user.hashed_password))
        assert not verify_password("OldPassword123!", str(user.hashed_password))

        # Verify reset token was cleared
        assert user.password_reset_token is None
        assert user.password_reset_token_expires is None

    def test_reset_user_password_user_not_found(self, sync_db_session: Session) -> None:
        """Test resetting password for non-existent user."""
        from app.crud.user import reset_user_password_sync

        # Try to reset password for non-existent user with valid UUID format
        fake_uuid = str(uuid.uuid4())
        success = reset_user_password_sync(
            sync_db_session, fake_uuid, "NewPassword123!"
        )
        assert success is False


@pytest.mark.skip(
    reason="Requires complex password reset workflow - not implemented yet"
)
class TestPasswordResetEmailService:
    def test_send_password_reset_email_success(self) -> None:
        """Test successful password reset email sending."""
        from app.services.email import email_service

        with (
            patch("app.services.email.email_service.is_configured", return_value=True),
            patch(
                "emails.Message.send",
                return_value=type("Response", (), {"status_code": 250})(),
            ),
        ):
            success = email_service.send_password_reset_email(
                "test@example.com", "testuser", "reset_token_123"
            )
            assert success is True

    def test_send_password_reset_email_not_configured(self) -> None:
        """Test password reset email sending when not configured."""
        from app.services.email import email_service

        with patch(
            "app.services.email.email_service.is_configured", return_value=False
        ):
            success = email_service.send_password_reset_email(
                "test@example.com", "testuser", "reset_token_123"
            )
            assert success is False

    def test_send_password_reset_email_send_failed(self) -> None:
        """Test password reset email sending failure."""
        from app.services.email import email_service

        with (
            patch("app.services.email.email_service.is_configured", return_value=True),
            patch(
                "emails.Message.send",
                return_value=type("Response", (), {"status_code": 500})(),
            ),
        ):
            success = email_service.send_password_reset_email(
                "test@example.com", "testuser", "reset_token_123"
            )
            assert success is False

    @pytest.mark.asyncio
    async def test_create_password_reset_token_success(
        self, sync_db_session: Session
    ) -> None:
        """Test successful password reset token creation."""
        from app.core.security import get_password_hash
        from app.models import User
        from app.services.email import email_service

        # Create user
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("TestPassword123!"),
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        # Create password reset token
        token = await email_service.create_password_reset_token(
            sync_db_session, str(user.id)
        )
        assert token is not None
        assert len(token) == 32  # Token should be 32 characters

        # Verify token was stored in database
        sync_db_session.refresh(user)
        assert user.password_reset_token == token
        assert user.password_reset_token_expires is not None
        assert user.password_reset_token_expires > datetime.now(timezone.utc)

    @pytest.mark.asyncio
    async def test_verify_password_reset_token_success(
        self, sync_db_session: Session
    ) -> None:
        """Test successful password reset token verification."""
        from app.core.security import get_password_hash
        from app.models import User
        from app.services.email import email_service

        # Create user with password reset token
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("TestPassword123!"),
            is_verified=True,
            password_reset_token="valid_reset_token",
            password_reset_token_expires=datetime.now(timezone.utc)
            + timedelta(hours=1),
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        # Verify token
        user_id = await email_service.verify_password_reset_token(
            sync_db_session, "valid_reset_token"
        )
        assert user_id == str(user.id)

    @pytest.mark.asyncio
    async def test_verify_password_reset_token_expired(
        self, sync_db_session: Session
    ) -> None:
        """Test password reset token verification with expired token."""
        from app.core.security import get_password_hash
        from app.models import User
        from app.services.email import email_service

        # Create user with expired password reset token
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("TestPassword123!"),
            is_verified=True,
            password_reset_token="expired_reset_token",
            password_reset_token_expires=datetime.now(timezone.utc)
            - timedelta(hours=1),
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        # Verify expired token
        user_id = await email_service.verify_password_reset_token(
            sync_db_session, "expired_reset_token"
        )
        assert user_id is None

    @pytest.mark.asyncio
    async def test_verify_password_reset_token_invalid(
        self, sync_db_session: Session
    ) -> None:
        """Test password reset token verification with invalid token."""
        from app.services.email import email_service

        # Verify invalid token
        user_id = await email_service.verify_password_reset_token(
            sync_db_session, "invalid_token"
        )
        assert user_id is None


@pytest.mark.skip(
    reason="Requires complex password reset workflow - not implemented yet"
)
class TestPasswordResetIntegration:
    def test_full_password_reset_flow(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test complete password reset flow from request to completion."""
        # Create user
        from app.core.security import get_password_hash
        from app.models import User

        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("OldPassword123!"),
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        # Step 1: Request password reset
        with patch(
            "app.services.email.email_service.send_password_reset_email",
            return_value=True,
        ):
            response = client.post(
                "/api/v1/auth/forgot-password", json={"email": "test@example.com"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["email_sent"] is True

        # Step 2: Get the reset token from the database
        sync_db_session.refresh(user)
        reset_token = user.password_reset_token
        assert reset_token is not None
        assert user.password_reset_token_expires is not None

        # Step 3: Reset password with token
        response = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": reset_token,
                "new_password": "NewPassword123!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["password_reset"] is True

        # Step 4: Verify password was changed by refreshing from database
        sync_db_session.refresh(user)

        # Test password verification directly
        from app.core.security import verify_password

        assert not verify_password("OldPassword123!", str(user.hashed_password))
        assert verify_password("NewPassword123!", str(user.hashed_password))

        # Step 5: Verify reset token was cleared
        assert user.password_reset_token is None
        assert user.password_reset_token_expires is None

        # Step 6: Verify authentication works with new password
        from app.crud.user import authenticate_user_sync

        # Old password should not work
        old_auth = authenticate_user_sync(
            sync_db_session, "test@example.com", "OldPassword123!"
        )
        assert old_auth is None

        # New password should work
        new_auth = authenticate_user_sync(
            sync_db_session, "test@example.com", "NewPassword123!"
        )
        assert new_auth is not None
        assert new_auth.email == "test@example.com"

        # Step 7: Verify user can login with new password
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "NewPassword123!"},
        )
        assert response.status_code == 200
        token_data = response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
