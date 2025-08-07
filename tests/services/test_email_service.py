"""
Tests for Email service.

This module tests the Email service functionality including email sending, token generation, and verification.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from app.services.email import EmailService


class TestEmailService:
    """Test Email service functionality."""

    def test_email_service_initialization(self):
        """Test Email service initialization."""
        email_service = EmailService()

        # Verify SMTP config is set
        assert "host" in email_service.smtp_config
        assert "port" in email_service.smtp_config
        assert "user" in email_service.smtp_config
        assert "password" in email_service.smtp_config
        assert "tls" in email_service.smtp_config
        assert "ssl" in email_service.smtp_config

    @patch("app.services.email.settings")
    def test_is_configured_true(self, mock_settings):
        """Test is_configured when all required settings are present."""
        # Mock settings
        mock_settings.SMTP_USERNAME = "test@example.com"
        mock_settings.SMTP_PASSWORD = "password123"
        mock_settings.SMTP_HOST = "smtp.example.com"

        email_service = EmailService()
        result = email_service.is_configured()

        assert result is True

    @patch("app.services.email.settings")
    def test_is_configured_false_missing_username(self, mock_settings):
        """Test is_configured when username is missing."""
        # Mock settings
        mock_settings.SMTP_USERNAME = None
        mock_settings.SMTP_PASSWORD = "password123"
        mock_settings.SMTP_HOST = "smtp.example.com"

        email_service = EmailService()
        result = email_service.is_configured()

        assert result is False

    @patch("app.services.email.settings")
    def test_is_configured_false_missing_password(self, mock_settings):
        """Test is_configured when password is missing."""
        # Mock settings
        mock_settings.SMTP_USERNAME = "test@example.com"
        mock_settings.SMTP_PASSWORD = None
        mock_settings.SMTP_HOST = "smtp.example.com"

        email_service = EmailService()
        result = email_service.is_configured()

        assert result is False

    @patch("app.services.email.settings")
    def test_is_configured_false_missing_host(self, mock_settings):
        """Test is_configured when host is missing."""
        # Mock settings
        mock_settings.SMTP_USERNAME = "test@example.com"
        mock_settings.SMTP_PASSWORD = "password123"
        mock_settings.SMTP_HOST = None

        email_service = EmailService()
        result = email_service.is_configured()

        assert result is False

    def test_generate_verification_token(self):
        """Test verification token generation."""
        email_service = EmailService()
        token = email_service.generate_verification_token()

        # Verify token is generated
        assert isinstance(token, str)
        assert len(token) == 32
        # Verify token contains alphanumeric characters
        assert all(c.isalnum() for c in token)

    @patch("app.services.email.settings")
    @patch("app.services.email.emails.Message")
    def test_send_verification_email_success(self, mock_message_class, mock_settings):
        """Test successful verification email sending."""
        # Mock settings
        mock_settings.SMTP_USERNAME = "test@example.com"
        mock_settings.SMTP_PASSWORD = "password123"
        mock_settings.SMTP_HOST = "smtp.example.com"
        mock_settings.FRONTEND_URL = "http://localhost:3000"
        mock_settings.PROJECT_NAME = "Test Project"
        mock_settings.FROM_NAME = "Test Sender"
        mock_settings.FROM_EMAIL = "test@example.com"
        mock_settings.VERIFICATION_TOKEN_EXPIRE_HOURS = 24

        # Mock email message
        mock_message = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 250
        mock_message.send.return_value = mock_response
        mock_message_class.return_value = mock_message

        email_service = EmailService()
        result = email_service.send_verification_email(
            "user@example.com",
            "testuser",
            "test-token-123",
        )

        # Verify result
        assert result is True

        # Verify message was created with correct parameters
        mock_message_class.assert_called_once()
        call_args = mock_message_class.call_args
        assert "Verify your email - Test Project" in call_args[1]["subject"]
        assert "testuser" in call_args[1]["html"]
        assert "test-token-123" in call_args[1]["html"]

        # Verify message was sent
        mock_message.send.assert_called_once()

    @patch("app.services.email.settings")
    def test_send_verification_email_not_configured(self, mock_settings):
        """Test verification email sending when not configured."""
        # Mock settings - missing required fields
        mock_settings.SMTP_USERNAME = None
        mock_settings.SMTP_PASSWORD = "password123"
        mock_settings.SMTP_HOST = "smtp.example.com"

        email_service = EmailService()
        result = email_service.send_verification_email(
            "user@example.com",
            "testuser",
            "test-token-123",
        )

        # Verify result
        assert result is False

    @patch("app.services.email.settings")
    @patch("app.services.email.emails.Message")
    def test_send_verification_email_send_error(
        self,
        mock_message_class,
        mock_settings,
    ):
        """Test verification email sending with send error."""
        # Mock settings
        mock_settings.SMTP_USERNAME = "test@example.com"
        mock_settings.SMTP_PASSWORD = "password123"
        mock_settings.SMTP_HOST = "smtp.example.com"
        mock_settings.FRONTEND_URL = "http://localhost:3000"
        mock_settings.PROJECT_NAME = "Test Project"
        mock_settings.FROM_NAME = "Test Sender"
        mock_settings.FROM_EMAIL = "test@example.com"
        mock_settings.VERIFICATION_TOKEN_EXPIRE_HOURS = 24

        # Mock email message to raise exception
        mock_message = MagicMock()
        mock_message.send.side_effect = Exception("Send failed")
        mock_message_class.return_value = mock_message

        email_service = EmailService()
        result = email_service.send_verification_email(
            "user@example.com",
            "testuser",
            "test-token-123",
        )

        # Verify result
        assert result is False

    @patch("app.services.email.settings")
    @patch("app.services.email.crud_user.update_verification_token_sync")
    async def test_create_verification_token_success(
        self,
        mock_update_token,
        mock_settings,
    ):
        """Test successful verification token creation."""
        # Mock settings
        mock_settings.VERIFICATION_TOKEN_EXPIRE_HOURS = 24

        # Mock database update
        mock_update_token.return_value = True

        email_service = EmailService()
        mock_db = MagicMock()
        result = await email_service.create_verification_token(mock_db, "user-123")

        # Verify result
        assert result is not None
        assert len(result) == 32

        # Verify database update was called
        mock_update_token.assert_called_once()
        call_args = mock_update_token.call_args
        assert call_args[1]["user_id"] == "user-123"
        assert call_args[1]["token"] == result
        assert isinstance(call_args[1]["expires"], datetime)

    @patch("app.services.email.settings")
    @patch("app.services.email.crud_user.update_verification_token_sync")
    async def test_create_verification_token_db_error(
        self,
        mock_update_token,
        mock_settings,
    ):
        """Test verification token creation with database error."""
        # Mock settings
        mock_settings.VERIFICATION_TOKEN_EXPIRE_HOURS = 24

        # Mock database update to fail
        mock_update_token.return_value = False

        email_service = EmailService()
        mock_db = MagicMock()
        result = await email_service.create_verification_token(mock_db, "user-123")

        # Verify result
        assert result is None

    @patch("app.services.email.crud_user.get_user_by_verification_token_sync")
    async def test_verify_token_success(self, mock_get_user):
        """Test successful token verification."""
        # Mock user found with proper datetime
        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.verification_token_expires = datetime.now(timezone.utc) + timedelta(
            hours=1,
        )
        mock_get_user.return_value = mock_user

        email_service = EmailService()
        mock_db = MagicMock()
        result = await email_service.verify_token(mock_db, "valid-token")

        # Verify result
        assert result == "user-123"

        # Verify database query was called
        mock_get_user.assert_called_once_with(mock_db, token="valid-token")

    @patch("app.services.email.crud_user.get_user_by_verification_token_sync")
    async def test_verify_token_invalid(self, mock_get_user):
        """Test token verification with invalid token."""
        # Mock user not found
        mock_get_user.return_value = None

        email_service = EmailService()
        mock_db = MagicMock()
        result = await email_service.verify_token(mock_db, "invalid-token")

        # Verify result
        assert result is None

    @patch("app.services.email.settings")
    @patch("app.services.email.emails.Message")
    def test_send_password_reset_email_success(self, mock_message_class, mock_settings):
        """Test successful password reset email sending."""
        # Mock settings
        mock_settings.SMTP_USERNAME = "test@example.com"
        mock_settings.SMTP_PASSWORD = "password123"
        mock_settings.SMTP_HOST = "smtp.example.com"
        mock_settings.FRONTEND_URL = "http://localhost:3000"
        mock_settings.PROJECT_NAME = "Test Project"
        mock_settings.FROM_NAME = "Test Sender"
        mock_settings.FROM_EMAIL = "test@example.com"

        # Mock email message
        mock_message = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 250
        mock_message.send.return_value = mock_response
        mock_message_class.return_value = mock_message

        email_service = EmailService()
        result = email_service.send_password_reset_email(
            "user@example.com",
            "testuser",
            "reset-token-123",
        )

        # Verify result
        assert result is True

        # Verify message was created
        mock_message_class.assert_called_once()
        call_args = mock_message_class.call_args
        assert "Password Reset Request" in call_args[1]["subject"]
        assert "testuser" in call_args[1]["html"]
        assert "reset-token-123" in call_args[1]["html"]

    @patch("app.services.email.settings")
    @patch("app.services.email.crud_user.update_password_reset_token_sync")
    async def test_create_password_reset_token_success(
        self,
        mock_update_token,
        mock_settings,
    ):
        """Test successful password reset token creation."""
        # Mock settings
        mock_settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS = 1

        # Mock database update
        mock_update_token.return_value = True

        email_service = EmailService()
        mock_db = MagicMock()
        result = await email_service.create_password_reset_token(mock_db, "user-123")

        # Verify result
        assert result is not None
        assert len(result) == 32

        # Verify database update was called
        mock_update_token.assert_called_once()

    @patch("app.services.email.crud_user.get_user_by_password_reset_token_sync")
    async def test_verify_password_reset_token_success(self, mock_get_user):
        """Test successful password reset token verification."""
        # Mock user found with proper datetime
        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.password_reset_token_expires = datetime.now(timezone.utc) + timedelta(
            hours=1,
        )
        mock_get_user.return_value = mock_user

        email_service = EmailService()
        mock_db = MagicMock()
        result = await email_service.verify_password_reset_token(mock_db, "valid-token")

        # Verify result
        assert result == "user-123"

    @patch("app.services.email.settings")
    @patch("app.services.email.emails.Message")
    def test_send_account_deletion_email_success(
        self,
        mock_message_class,
        mock_settings,
    ):
        """Test successful account deletion email sending."""
        # Mock settings
        mock_settings.SMTP_USERNAME = "test@example.com"
        mock_settings.SMTP_PASSWORD = "password123"
        mock_settings.SMTP_HOST = "smtp.example.com"
        mock_settings.FRONTEND_URL = "http://localhost:3000"
        mock_settings.PROJECT_NAME = "Test Project"
        mock_settings.FROM_NAME = "Test Sender"
        mock_settings.FROM_EMAIL = "test@example.com"

        # Mock email message
        mock_message = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 250
        mock_message.send.return_value = mock_response
        mock_message_class.return_value = mock_message

        email_service = EmailService()
        result = email_service.send_account_deletion_email(
            "user@example.com",
            "testuser",
            "deletion-token-123",
        )

        # Verify result
        assert result is True

        # Verify message was created
        mock_message_class.assert_called_once()
        call_args = mock_message_class.call_args
        assert "Account Deletion Request" in call_args[1]["subject"]
        assert "testuser" in call_args[1]["html"]
        assert "deletion-token-123" in call_args[1]["html"]

    @patch("app.services.email.settings")
    @patch("app.services.email.emails.Message")
    def test_send_account_deletion_reminder_email_success(
        self,
        mock_message_class,
        mock_settings,
    ):
        """Test successful account deletion reminder email sending."""
        # Mock settings
        mock_settings.SMTP_USERNAME = "test@example.com"
        mock_settings.SMTP_PASSWORD = "password123"
        mock_settings.SMTP_HOST = "smtp.example.com"
        mock_settings.PROJECT_NAME = "Test Project"
        mock_settings.FROM_NAME = "Test Sender"
        mock_settings.FROM_EMAIL = "test@example.com"

        # Mock email message
        mock_message = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 250
        mock_message.send.return_value = mock_response
        mock_message_class.return_value = mock_message

        email_service = EmailService()
        result = email_service.send_account_deletion_reminder_email(
            "user@example.com",
            "testuser",
            5,
            "2023-12-31",
        )

        # Verify result
        assert result is True

        # Verify message was created
        mock_message_class.assert_called_once()
        call_args = mock_message_class.call_args
        assert "Account Deletion Reminder" in call_args[1]["subject"]
        assert "testuser" in call_args[1]["html"]
        assert "5 day(s)" in call_args[1]["html"]

    @patch("app.services.email.settings")
    @patch("app.services.email.crud_user.update_deletion_token_sync")
    async def test_create_deletion_token_success(
        self,
        mock_update_token,
        mock_settings,
    ):
        """Test successful deletion token creation."""
        # Mock settings
        mock_settings.ACCOUNT_DELETION_TOKEN_EXPIRE_HOURS = 24

        # Mock database update
        mock_update_token.return_value = True

        email_service = EmailService()
        mock_db = MagicMock()
        result = await email_service.create_deletion_token(mock_db, "user-123")

        # Verify result
        assert result is not None
        assert len(result) == 32

        # Verify database update was called
        mock_update_token.assert_called_once()

    @patch("app.services.email.crud_user.get_user_by_deletion_token_sync")
    async def test_verify_deletion_token_success(self, mock_get_user):
        """Test successful deletion token verification."""
        # Mock user found with proper datetime
        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.deletion_token_expires = datetime.now(timezone.utc) + timedelta(
            hours=1,
        )
        mock_get_user.return_value = mock_user

        email_service = EmailService()
        mock_db = MagicMock()
        result = await email_service.verify_deletion_token(mock_db, "valid-token")

        # Verify result
        assert result == "user-123"


class TestEmailServiceIntegration:
    """Test Email service integration scenarios."""

    @patch("app.services.email.settings")
    @patch("app.services.email.emails.Message")
    @patch("app.services.email.crud_user.update_verification_token_sync")
    @patch("app.services.email.crud_user.get_user_by_verification_token_sync")
    async def test_email_verification_lifecycle(
        self,
        mock_get_user,
        mock_update_token,
        mock_message_class,
        mock_settings,
    ):
        """Test complete email verification lifecycle."""
        # Mock settings
        mock_settings.SMTP_USERNAME = "test@example.com"
        mock_settings.SMTP_PASSWORD = "password123"
        mock_settings.SMTP_HOST = "smtp.example.com"
        mock_settings.FRONTEND_URL = "http://localhost:3000"
        mock_settings.PROJECT_NAME = "Test Project"
        mock_settings.FROM_NAME = "Test Sender"
        mock_settings.FROM_EMAIL = "test@example.com"
        mock_settings.VERIFICATION_TOKEN_EXPIRE_HOURS = 24

        # Mock email message
        mock_message = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 250
        mock_message.send.return_value = mock_response
        mock_message_class.return_value = mock_message

        # Mock database operations
        mock_update_token.return_value = True
        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.verification_token_expires = datetime.now(timezone.utc) + timedelta(
            hours=1,
        )
        mock_get_user.return_value = mock_user

        email_service = EmailService()
        mock_db = MagicMock()

        # Test token creation
        token = await email_service.create_verification_token(mock_db, "user-123")
        assert token is not None

        # Test email sending
        email_sent = email_service.send_verification_email(
            "user@example.com",
            "testuser",
            token,
        )
        assert email_sent is True

        # Test token verification
        user_id = await email_service.verify_token(mock_db, token)
        assert user_id == "user-123"
