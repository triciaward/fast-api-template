from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.fixture(autouse=True)
def always_configured_email(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch email service to always be configured for all tests in this file."""
    monkeypatch.setattr("app.services.email.email_service.is_configured", lambda: True)


class TestEmailVerificationEndpoints:
    def test_register_user_with_email_verification(self, client: TestClient) -> None:
        """Test user registration with email verification."""
        with patch(
            "app.services.email.email_service.is_configured", return_value=True
        ), patch(
            "app.services.email.email_service.send_verification_email",
            return_value=True,
        ):
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "test@example.com",
                    "username": "testuser",
                    "password": "TestPassword123!",
                },
            )
            assert response.status_code == 201
            user_data = response.json()
            assert user_data["email"] == "test@example.com"
            assert user_data["username"] == "testuser"
            assert user_data["is_verified"] is False

    def test_register_user_email_not_configured(self, client: TestClient) -> None:
        """Test user registration when email is not configured."""
        with patch(
            "app.services.email.email_service.is_configured", return_value=False
        ):
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "test@example.com",
                    "username": "testuser",
                    "password": "TestPassword123!",
                },
            )
            assert response.status_code == 201
            user_data = response.json()
            assert user_data["is_verified"] is False

    def test_login_unverified_user(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test login attempt by unverified user."""
        # Create unverified user
        from app.core.security import get_password_hash
        from app.models.models import User

        user = User(
            email="unverified@example.com",
            username="unverifieduser",
            hashed_password=get_password_hash("TestPassword123!"),
            is_verified=False,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            data={"username": "unverified@example.com", "password": "TestPassword123!"},
        )
        assert response.status_code == 401
        assert "Please verify your email before logging in" in response.json()["detail"]

    def test_login_verified_user(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test successful login by verified user."""
        # Create verified user
        from app.core.security import get_password_hash
        from app.models.models import User

        user = User(
            email="verified@example.com",
            username="verifieduser",
            hashed_password=get_password_hash("TestPassword123!"),
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            data={"username": "verified@example.com", "password": "TestPassword123!"},
        )
        assert response.status_code == 200
        token_data = response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"

    def test_resend_verification_email_success(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test successful resend verification email."""
        # Create unverified user
        from app.models.models import User

        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            is_verified=False,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        with patch(
            "app.services.email.email_service.is_configured", return_value=True
        ), patch(
            "app.services.email.email_service.send_verification_email",
            return_value=True,
        ):
            response = client.post(
                "/api/v1/auth/resend-verification", json={"email": "test@example.com"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Verification email sent successfully"
            assert data["email_sent"] is True

    def test_resend_verification_email_user_not_found(self, client: TestClient) -> None:
        """Test resend verification email for non-existent user."""
        response = client.post(
            "/api/v1/auth/resend-verification",
            json={"email": "nonexistent@example.com"},
        )
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    def test_resend_verification_email_already_verified(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test resend verification email for already verified user."""
        # Create verified user
        from app.models.models import User

        user = User(
            email="verified@example.com",
            username="verifieduser",
            hashed_password="hashed_password",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        response = client.post(
            "/api/v1/auth/resend-verification", json={"email": "verified@example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "User is already verified"
        assert data["email_sent"] is False

    def test_resend_verification_email_not_configured(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test resend verification email when email is not configured."""
        # Create unverified user
        from app.models.models import User

        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            is_verified=False,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        with patch(
            "app.services.email.email_service.is_configured", return_value=False
        ):
            response = client.post(
                "/api/v1/auth/resend-verification", json={"email": "test@example.com"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Email service not configured"
            assert data["email_sent"] is False

    def test_verify_email_success(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test successful email verification."""
        # Create user with verification token
        from app.models.models import User

        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            verification_token="test_token",
            verification_token_expires=datetime.utcnow() + timedelta(hours=1),
            is_verified=False,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        response = client.post(
            "/api/v1/auth/verify-email", json={"token": "test_token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Email verified successfully"
        assert data["verified"] is True

    def test_verify_email_invalid_token(self, client: TestClient) -> None:
        """Test email verification with invalid token."""
        response = client.post(
            "/api/v1/auth/verify-email", json={"token": "invalid_token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Invalid or expired verification token"
        assert data["verified"] is False


class TestEmailVerificationCRUDOperations:
    def test_get_user_by_verification_token_sync(
        self, sync_db_session: Session
    ) -> None:
        """Test getting user by verification token using sync CRUD."""
        from app.crud import user as crud_user
        from app.models.models import User

        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            verification_token="test_token",
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        found_user = crud_user.get_user_by_verification_token_sync(
            sync_db_session, "test_token"
        )
        assert found_user is not None
        assert found_user.email == "test@example.com"

    def test_update_verification_token_sync(self, sync_db_session: Session) -> None:
        """Test updating verification token using sync CRUD."""
        from app.crud import user as crud_user
        from app.models.models import User

        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        expires = datetime.utcnow() + timedelta(hours=1)
        success = crud_user.update_verification_token_sync(
            sync_db_session, str(user.id), "new_token", expires
        )
        assert success is True

        # Verify the token was updated
        sync_db_session.refresh(user)
        assert user.verification_token == "new_token"

    def test_update_verification_token_user_not_found(
        self, sync_db_session: Session
    ) -> None:
        """Test updating verification token for non-existent user."""
        import uuid

        from app.crud import user as crud_user

        non_existent_uuid = str(uuid.uuid4())
        expires = datetime.utcnow() + timedelta(hours=1)
        success = crud_user.update_verification_token_sync(
            sync_db_session, non_existent_uuid, "new_token", expires
        )
        assert success is False

    def test_verify_user_sync(self, sync_db_session: Session) -> None:
        """Test verifying user using sync CRUD."""
        from app.crud import user as crud_user
        from app.models.models import User

        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            verification_token="test_token",
            is_verified=False,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        success = crud_user.verify_user_sync(sync_db_session, str(user.id))
        assert success is True

        # Verify the user was marked as verified
        sync_db_session.refresh(user)
        assert user.is_verified is True
        assert user.verification_token is None  # type: ignore[unreachable]

    def test_verify_user_not_found(self, sync_db_session: Session) -> None:
        """Test verifying non-existent user."""
        import uuid

        from app.crud import user as crud_user

        non_existent_uuid = str(uuid.uuid4())
        success = crud_user.verify_user_sync(sync_db_session, non_existent_uuid)
        assert success is False


class TestEmailVerificationIntegration:
    def test_full_email_verification_flow(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test complete email verification flow."""
        with patch(
            "app.services.email.email_service.is_configured", return_value=True
        ), patch(
            "app.services.email.email_service.send_verification_email",
            return_value=True,
        ):
            # Step 1: Register user
            register_response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "flow@example.com",
                    "username": "flowuser",
                    "password": "TestPassword123!",
                },
            )
            assert register_response.status_code == 201
            user_data = register_response.json()
            assert user_data["is_verified"] is False

            # Step 2: Try to login (should fail)
            login_response = client.post(
                "/api/v1/auth/login",
                data={"username": "flow@example.com", "password": "TestPassword123!"},
            )
            assert login_response.status_code == 401
            assert (
                "Please verify your email before logging in"
                in login_response.json()["detail"]
            )

            # Step 3: Get the user and manually set verification token
            from app.models.models import User

            user = (
                sync_db_session.query(User)
                .filter(User.email == "flow@example.com")
                .first()
            )
            assert user is not None

            # Set verification token manually
            user.verification_token = "test_verification_token"  # type: ignore
            user.verification_token_expires = datetime.utcnow() + timedelta(hours=1)  # type: ignore
            sync_db_session.commit()

        # Step 4: Verify email
        verify_response = client.post(
            "/api/v1/auth/verify-email", json={"token": "test_verification_token"}
        )
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        assert verify_data["verified"] is True

        # Step 5: Login should now succeed
        final_login_response = client.post(
            "/api/v1/auth/login",
            data={"username": "flow@example.com", "password": "TestPassword123!"},
        )
        assert final_login_response.status_code == 200
        token_data = final_login_response.json()
        assert "access_token" in token_data
