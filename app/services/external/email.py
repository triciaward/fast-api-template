import secrets
import string
from datetime import datetime, timedelta, timezone

import emails
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud import (
    get_user_by_deletion_token,
    get_user_by_password_reset_token,
    get_user_by_verification_token,
    update_deletion_token,
    update_password_reset_token,
    update_verification_token,
)


def utc_now() -> datetime:
    """Get current UTC datetime (replaces deprecated utc_now())."""
    return datetime.now(timezone.utc)


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
            settings.SMTP_USERNAME and settings.SMTP_PASSWORD and settings.SMTP_HOST,
        )

    def generate_verification_token(self) -> str:
        """Generate a secure verification token."""
        return "".join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(32)
        )

    def send_verification_email(
        self,
        email: str,
        username: str,
        verification_token: str,
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
        except Exception:
            return False
        else:
            return response.status_code == 250  # type: ignore

    async def create_verification_token(self, db: AsyncSession, user_id: str) -> str | None:
        """Create and store verification token for a user."""
        token = self.generate_verification_token()
        expires = utc_now() + timedelta(hours=settings.VERIFICATION_TOKEN_EXPIRE_HOURS)

        success = await update_verification_token(
            db,
            user_id=user_id,
            token=token,
            expires=expires,
        )

        return token if success else None

    async def verify_token(self, db: AsyncSession, token: str) -> str | None:
        """Verify a verification token and return user ID if valid."""
        user = await get_user_by_verification_token(db, token=token)
        if not user:
            return None

        # Check if token is expired
        if (
            user.verification_token_expires
            and user.verification_token_expires < utc_now()
        ):
            return None

        # Return user ID for verification
        return str(user.id)

    def send_password_reset_email(
        self,
        email: str,
        username: str,
        reset_token: str,
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
        except Exception:
            return False
        else:
            return response.status_code == 250  # type: ignore

    async def create_password_reset_token(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> str | None:
        """Create and store password reset token for a user."""
        token = self.generate_verification_token()
        expires = utc_now() + timedelta(
            hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS,
        )

        success = await update_password_reset_token(
            db,
            user_id=user_id,
            token=token,
            expires=expires,
        )

        return token if success else None

    async def verify_password_reset_token(self, db: AsyncSession, token: str) -> str | None:
        """Verify a password reset token and return user ID if valid."""
        user = await get_user_by_password_reset_token(db, token=token)
        if not user:
            return None

        # Check if token is expired
        if (
            user.password_reset_token_expires
            and user.password_reset_token_expires < utc_now()
        ):
            return None

        # Return user ID for password reset
        return str(user.id)

    def send_account_deletion_email(
        self,
        email: str,
        username: str,
        deletion_token: str,
    ) -> bool:
        """Send account deletion confirmation email."""
        if not self.is_configured():
            return False

        deletion_url = (
            f"{settings.FRONTEND_URL}/confirm-deletion?token={deletion_token}"
        )

        # HTML template for account deletion confirmation
        html_content = f"""
        <html>
        <body>
            <h2>Confirm Your Account Deletion Request - {settings.PROJECT_NAME}</h2>
            <p>Hi {username},</p>
            <p>We received a request to delete your account. To confirm this action, please click the link below:</p>
            <p><a href="{deletion_url}">Confirm Account Deletion</a></p>
            <p>If the link doesn't work, copy and paste this URL into your browser:</p>
            <p>{deletion_url}</p>
            <p><strong>Important:</strong> This link will expire in {settings.ACCOUNT_DELETION_TOKEN_EXPIRE_HOURS} hours.</p>
            <p>After confirmation, your account will be scheduled for deletion in {settings.ACCOUNT_DELETION_GRACE_PERIOD_DAYS} days. During this time, you can still log in and cancel the deletion.</p>
            <p>If you didn't request this deletion, please ignore this email or contact support immediately.</p>
            <br>
            <p>Best regards,<br>{settings.FROM_NAME}</p>
        </body>
        </html>
        """

        message = emails.Message(
            subject=f"Confirm Your Account Deletion Request - {settings.PROJECT_NAME}",
            html=html_content,
            mail_from=(settings.FROM_NAME, settings.FROM_EMAIL),
        )

        try:
            response = message.send(
                to=email,
                smtp=self.smtp_config,
            )
        except Exception:
            return False
        else:
            return response.status_code == 250  # type: ignore

    def send_account_deletion_reminder_email(
        self,
        email: str,
        username: str,
        days_remaining: int,
        deletion_date: str,
    ) -> bool:
        """Send account deletion reminder email."""
        if not self.is_configured():
            return False

        cancel_url = f"{settings.FRONTEND_URL}/cancel-deletion"

        # HTML template for account deletion reminder
        html_content = f"""
        <html>
        <body>
            <h2>Your Account Will Be Deleted Soon - {settings.PROJECT_NAME}</h2>
            <p>Hi {username},</p>
            <p>Your account is scheduled for deletion on <strong>{deletion_date}</strong> ({days_remaining} day(s) remaining).</p>
            <p>To cancel this deletion and keep your account, please log in to your account and go to Settings > Account.</p>
            <p><a href="{cancel_url}">Cancel Account Deletion</a></p>
            <p>If you don't take action, your account and all associated data will be permanently removed.</p>
            <p>This action cannot be undone once the deletion is complete.</p>
            <br>
            <p>Best regards,<br>{settings.FROM_NAME}</p>
        </body>
        </html>
        """

        message = emails.Message(
            subject=f"Account Deletion Reminder - {days_remaining} Day(s) Remaining - {settings.PROJECT_NAME}",
            html=html_content,
            mail_from=(settings.FROM_NAME, settings.FROM_EMAIL),
        )

        try:
            response = message.send(
                to=email,
                smtp=self.smtp_config,
            )
        except Exception:
            return False
        else:
            return response.status_code == 250  # type: ignore

    async def create_deletion_token(self, db: AsyncSession, user_id: str) -> str | None:
        """Create and store deletion token for a user."""
        token = self.generate_verification_token()
        expires = utc_now() + timedelta(
            hours=settings.ACCOUNT_DELETION_TOKEN_EXPIRE_HOURS,
        )

        success = await update_deletion_token(
            db,
            user_id=user_id,
            token=token,
            expires=expires,
        )

        return token if success else None

    async def verify_deletion_token(self, db: AsyncSession, token: str) -> str | None:
        """Verify a deletion token and return user ID if valid."""
        user = await get_user_by_deletion_token(db, token=token)
        if not user:
            return None

        # Check if token is expired
        if user.deletion_token_expires and user.deletion_token_expires < utc_now():
            return None

        # Return user ID for deletion confirmation
        return str(user.id)


email_service = EmailService()
