import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.core.validation import (
    clean_input,
    sanitize_input,
    validate_email_format,
    validate_password,
    validate_username,
)


class UserBase(BaseModel):
    email: EmailStr
    username: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format and check for disposable domains."""
        is_valid, error_msg = validate_email_format(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v.lower().strip()

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format and content."""
        # Clean first to remove whitespace and control characters
        v = clean_input(v)

        # Then validate (including length)
        is_valid, error_msg = validate_username(v)
        if not is_valid:
            raise ValueError(error_msg)

        return v


class UserCreate(UserBase):
    password: str
    is_superuser: bool = False

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        is_valid, error_msg = validate_password(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        is_valid, error_msg = validate_email_format(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v.lower().strip()


class UserResponse(UserBase):
    id: uuid.UUID
    is_superuser: bool
    is_verified: bool
    date_created: datetime
    oauth_provider: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# OAuth schemas
class OAuthLogin(BaseModel):
    provider: str  # 'google' or 'apple'
    access_token: str

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate OAuth provider."""
        if v.lower() not in ["google", "apple"]:
            raise ValueError("Provider must be 'google' or 'apple'")
        return v.lower()


class OAuthUserInfo(BaseModel):
    provider: str
    oauth_id: str
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None


# Email verification schemas
class EmailVerificationRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        is_valid, error_msg = validate_email_format(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v.lower().strip()


class EmailVerificationResponse(BaseModel):
    message: str
    email_sent: bool


class VerifyEmailRequest(BaseModel):
    token: str

    @field_validator("token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        """Sanitize verification token."""
        return sanitize_input(v, max_length=255)


class VerifyEmailResponse(BaseModel):
    message: str
    verified: bool


# Password reset schemas
class PasswordResetRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        is_valid, error_msg = validate_email_format(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v.lower().strip()


class PasswordResetResponse(BaseModel):
    message: str
    email_sent: bool


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        """Sanitize reset token."""
        return sanitize_input(v, max_length=255)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength."""
        is_valid, error_msg = validate_password(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


class PasswordResetConfirmResponse(BaseModel):
    message: str
    password_reset: bool


# Account deletion schemas (GDPR compliance)
class AccountDeletionRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        is_valid, error_msg = validate_email_format(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v.lower().strip()


class AccountDeletionResponse(BaseModel):
    message: str
    email_sent: bool


class AccountDeletionConfirmRequest(BaseModel):
    token: str

    @field_validator("token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        """Sanitize deletion token."""
        return sanitize_input(v, max_length=255)


class AccountDeletionConfirmResponse(BaseModel):
    message: str
    deletion_confirmed: bool
    deletion_scheduled_for: datetime


class AccountDeletionCancelRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        is_valid, error_msg = validate_email_format(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v.lower().strip()


class AccountDeletionCancelResponse(BaseModel):
    message: str
    deletion_cancelled: bool


class AccountDeletionStatusResponse(BaseModel):
    deletion_requested: bool
    deletion_confirmed: bool
    deletion_scheduled_for: Optional[datetime] = None
    can_cancel: bool
    grace_period_days: int
