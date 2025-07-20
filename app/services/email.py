import secrets
import string
from datetime import datetime, timedelta
from typing import Optional

import emails
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud import user as crud_user


class EmailService:
    def __init__(self) -> None:
        self.smtp_config = {
            "host": settings.SMTP_HOST,
            "port": settings.SMTP_PORT,
            "user": settings.SMTP_USERNAME,
            "password": settings.SMTP_PASSWORD,
            "tls": settings.SMTP_TLS,
            "ssl": settings.SMTP_SSL,
        }

    def is_configured(self) -> bool:
        """Check if email service is properly configured."""
        return bool(
            settings.SMTP_USERNAME and settings.SMTP_PASSWORD and settings.SMTP_HOST
        )

    def generate_verification_token(self) -> str:
        """Generate a secure verification token."""
        return "".join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(32)
        )

    def send_verification_email(
        self, email: str, username: str, verification_token: str
    ) -> bool:
        """Send email verification email."""
        if not self.is_configured():
            return False

        verification_url = (
            f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
        )

        # Simple HTML template
        html_content = f"""
        <html>
        <body>
            <h2>Welcome to {settings.PROJECT_NAME}!</h2>
            <p>Hi {username},</p>
            <p>Thank you for signing up! Please verify your email address by clicking the link below:</p>
            <p><a href="{verification_url}">Verify Email Address</a></p>
            <p>If the link doesn't work, copy and paste this URL into your browser:</p>
            <p>{verification_url}</p>
            <p>This link will expire in {settings.VERIFICATION_TOKEN_EXPIRE_HOURS} hours.</p>
            <p>If you didn't create an account, you can safely ignore this email.</p>
            <br>
            <p>Best regards,<br>{settings.FROM_NAME}</p>
        </body>
        </html>
        """

        message = emails.Message(
            subject=f"Verify your email - {settings.PROJECT_NAME}",
            html=html_content,
            mail_from=(settings.FROM_NAME, settings.FROM_EMAIL),
        )

        try:
            response = message.send(
                to=email,
                smtp=self.smtp_config,
            )
            return response.status_code == 250  # type: ignore
        except Exception:
            return False

    async def create_verification_token(
        self, db: Session, user_id: str
    ) -> Optional[str]:
        """Create and store verification token for a user."""
        token = self.generate_verification_token()
        expires = datetime.utcnow() + timedelta(
            hours=settings.VERIFICATION_TOKEN_EXPIRE_HOURS
        )

        success = crud_user.update_verification_token_sync(
            db, user_id=user_id, token=token, expires=expires
        )

        return token if success else None

    async def verify_token(self, db: Session, token: str) -> Optional[str]:
        """Verify a verification token and return user ID if valid."""
        user = crud_user.get_user_by_verification_token_sync(db, token=token)
        if not user:
            return None

        # Check if token is expired
        if (
            user.verification_token_expires
            and user.verification_token_expires < datetime.utcnow()
        ):
            return None

        # Return user ID for verification
        return str(user.id)

    def send_password_reset_email(
        self, email: str, username: str, reset_token: str
    ) -> bool:
        """Send password reset email."""
        if not self.is_configured():
            return False

        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

        # Simple HTML template
        html_content = f"""
        <html>
        <body>
            <h2>Password Reset Request - {settings.PROJECT_NAME}</h2>
            <p>Hi {username},</p>
            <p>We received a request to reset your password. Click the link below to create a new password:</p>
            <p><a href="{reset_url}">Reset Password</a></p>
            <p>If the link doesn't work, copy and paste this URL into your browser:</p>
            <p>{reset_url}</p>
            <p>This link will expire in {settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS} hour(s).</p>
            <p>If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.</p>
            <br>
            <p>Best regards,<br>{settings.FROM_NAME}</p>
        </body>
        </html>
        """

        message = emails.Message(
            subject=f"Password Reset Request - {settings.PROJECT_NAME}",
            html=html_content,
            mail_from=(settings.FROM_NAME, settings.FROM_EMAIL),
        )

        try:
            response = message.send(
                to=email,
                smtp=self.smtp_config,
            )
            return response.status_code == 250  # type: ignore
        except Exception:
            return False

    async def create_password_reset_token(
        self, db: Session, user_id: str
    ) -> Optional[str]:
        """Create and store password reset token for a user."""
        token = self.generate_verification_token()
        expires = datetime.utcnow() + timedelta(
            hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS
        )

        success = crud_user.update_password_reset_token_sync(
            db, user_id=user_id, token=token, expires=expires
        )

        return token if success else None

    async def verify_password_reset_token(
        self, db: Session, token: str
    ) -> Optional[str]:
        """Verify a password reset token and return user ID if valid."""
        user = crud_user.get_user_by_password_reset_token_sync(db, token=token)
        if not user:
            return None

        # Check if token is expired
        if (
            user.password_reset_token_expires
            and user.password_reset_token_expires < datetime.utcnow()
        ):
            return None

        # Return user ID for password reset
        return str(user.id)


email_service = EmailService()
