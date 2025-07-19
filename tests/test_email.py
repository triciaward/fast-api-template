from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.services.email import email_service


class TestEmailService:
    def test_init(self) -> None:
        """Test EmailService initialization."""
        assert email_service is not None
        assert hasattr(email_service, "smtp_config")

    @patch("app.services.email.settings")
    def test_is_configured_true(self, mock_settings: MagicMock) -> None:
        """Test is_configured when all settings are present."""
        mock_settings.SMTP_USERNAME = "test_user"
        mock_settings.SMTP_PASSWORD = "test_password"
        mock_settings.SMTP_HOST = "test_host"

        assert email_service.is_configured() is True

    @patch("app.services.email.settings")
    def test_is_configured_false_no_username(self, mock_settings: MagicMock) -> None:
        """Test is_configured when username is missing."""
        mock_settings.SMTP_USERNAME = None
        mock_settings.SMTP_PASSWORD = "test_password"
        mock_settings.SMTP_HOST = "test_host"

        assert email_service.is_configured() is False

    @patch("app.services.email.settings")
    def test_is_configured_false_no_password(self, mock_settings: MagicMock) -> None:
        """Test is_configured when password is missing."""
        mock_settings.SMTP_USERNAME = "test_user"
        mock_settings.SMTP_PASSWORD = None
        mock_settings.SMTP_HOST = "test_host"

        assert email_service.is_configured() is False

    @patch("app.services.email.settings")
    def test_is_configured_false_no_host(self, mock_settings: MagicMock) -> None:
        """Test is_configured when host is missing."""
        mock_settings.SMTP_USERNAME = "test_user"
        mock_settings.SMTP_PASSWORD = "test_password"
        mock_settings.SMTP_HOST = None

        assert email_service.is_configured() is False

    def test_generate_verification_token(self) -> None:
        """Test verification token generation."""
        token = email_service.generate_verification_token()
        assert isinstance(token, str)
        assert len(token) == 32
        assert all(c.isalnum() for c in token)

    @patch("app.services.email.settings")
    def test_send_verification_email_not_configured(
        self, mock_settings: MagicMock
    ) -> None:
        """Test send_verification_email when not configured."""
        mock_settings.SMTP_USERNAME = None
        mock_settings.SMTP_PASSWORD = "test_password"
        mock_settings.SMTP_HOST = "test_host"

        result = email_service.send_verification_email(
            "test@example.com", "testuser", "test_token"
        )
        assert result is False

    @patch("app.services.email.settings")
    @patch("app.services.email.emails.Message")
    def test_send_verification_email_success(
        self, mock_message_class: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test successful email sending."""
        mock_settings.SMTP_USERNAME = "test_user"
        mock_settings.SMTP_PASSWORD = "test_password"
        mock_settings.SMTP_HOST = "test_host"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_TLS = True
        mock_settings.SMTP_SSL = False
        mock_settings.FRONTEND_URL = "http://localhost:3000"
        mock_settings.PROJECT_NAME = "Test Project"
        mock_settings.FROM_NAME = "Test App"
        mock_settings.FROM_EMAIL = "noreply@test.com"
        mock_settings.VERIFICATION_TOKEN_EXPIRE_HOURS = 24

        mock_message = MagicMock()
        mock_message_class.return_value = mock_message
        mock_message.send.return_value.status_code = 250

        result = email_service.send_verification_email(
            "test@example.com", "testuser", "test_token"
        )
        assert result is True

    @patch("app.services.email.settings")
    @patch("app.services.email.emails.Message")
    def test_send_verification_email_failure(
        self, mock_message_class: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test email sending failure."""
        mock_settings.SMTP_USERNAME = "test_user"
        mock_settings.SMTP_PASSWORD = "test_password"
        mock_settings.SMTP_HOST = "test_host"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_TLS = True
        mock_settings.SMTP_SSL = False
        mock_settings.FRONTEND_URL = "http://localhost:3000"
        mock_settings.PROJECT_NAME = "Test Project"
        mock_settings.FROM_NAME = "Test App"
        mock_settings.FROM_EMAIL = "noreply@test.com"
        mock_settings.VERIFICATION_TOKEN_EXPIRE_HOURS = 24

        mock_message = MagicMock()
        mock_message_class.return_value = mock_message
        mock_message.send.side_effect = Exception("SMTP error")

        result = email_service.send_verification_email(
            "test@example.com", "testuser", "test_token"
        )
        assert result is False

    @patch("app.services.email.settings")
    @patch("app.services.email.emails.Message")
    def test_send_verification_email_wrong_status_code(
        self, mock_message_class: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test email sending with wrong status code."""
        mock_settings.SMTP_USERNAME = "test_user"
        mock_settings.SMTP_PASSWORD = "test_password"
        mock_settings.SMTP_HOST = "test_host"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_TLS = True
        mock_settings.SMTP_SSL = False
        mock_settings.FRONTEND_URL = "http://localhost:3000"
        mock_settings.PROJECT_NAME = "Test Project"
        mock_settings.FROM_NAME = "Test App"
        mock_settings.FROM_EMAIL = "noreply@test.com"
        mock_settings.VERIFICATION_TOKEN_EXPIRE_HOURS = 24

        mock_message = MagicMock()
        mock_message_class.return_value = mock_message
        mock_message.send.return_value.status_code = 500

        result = email_service.send_verification_email(
            "test@example.com", "testuser", "test_token"
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_create_verification_token_success(
        self, sync_db_session: Session
    ) -> None:
        """Test creating verification token successfully."""
        # Create a test user first
        from app.models.models import User

        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        token = await email_service.create_verification_token(
            sync_db_session, str(user.id)
        )
        assert token is not None
        assert isinstance(token, str)

    @pytest.mark.asyncio
    async def test_create_verification_token_failure(
        self, sync_db_session: Session
    ) -> None:
        """Test creating verification token failure."""
        import uuid

        non_existent_uuid = str(uuid.uuid4())
        token = await email_service.create_verification_token(
            sync_db_session, non_existent_uuid
        )
        assert token is None

    @pytest.mark.asyncio
    async def test_verify_token_success(self, sync_db_session: Session) -> None:
        """Test token verification successfully."""
        # Create a test user with verification token
        from app.models.models import User

        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            verification_token="test_token",
            verification_token_expires=datetime.utcnow() + timedelta(hours=1),
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        result = await email_service.verify_token(sync_db_session, "test_token")
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_token_user_not_found(self, sync_db_session: Session) -> None:
        """Test token verification when user not found."""
        result = await email_service.verify_token(sync_db_session, "non_existent_token")
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_token_expired(self, sync_db_session: Session) -> None:
        """Test token verification with expired token."""
        # Create a test user with expired verification token
        from app.models.models import User

        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            verification_token="expired_token",
            verification_token_expires=datetime.utcnow() - timedelta(hours=1),
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        result = await email_service.verify_token(sync_db_session, "expired_token")
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_token_verification_failure(
        self, sync_db_session: Session
    ) -> None:
        """Test token verification when verification fails."""
        # Create a test user with verification token
        from app.models.models import User

        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            verification_token="test_token",
            verification_token_expires=datetime.utcnow() + timedelta(hours=1),
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        # Mock the verify_user_sync to return False
        with patch("app.crud.user.verify_user_sync", return_value=False):
            result = await email_service.verify_token(sync_db_session, "test_token")
            assert result is False


class TestEmailServiceIntegration:
    def test_email_service_singleton(self) -> None:
        """Test that email_service is a singleton."""
        from app.services.email import email_service as email_service2

        assert email_service is email_service2
