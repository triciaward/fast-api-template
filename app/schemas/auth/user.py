import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SerializationInfo,
    field_serializer,
    field_validator,
)

from app.core.security.validation import (
    clean_input,
    sanitize_input,
    validate_email_format,
    validate_password,
    validate_username,
)
from app.utils.pagination import PaginatedResponse


class ScopesTypeError(TypeError):
    """Raised when scopes is not a list."""


class InvalidScopeError(ValueError):
    """Raised when a scope is invalid."""


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
    created_at: datetime  # Fixed: was date_created
    oauth_provider: str | None = None
    # Soft delete fields
    is_deleted: bool
    deleted_at: datetime | None = None
    deleted_by: uuid.UUID | None = None
    deletion_reason: str | None = None

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int  # seconds until access token expires


class SessionInfo(BaseModel):
    id: uuid.UUID
    created_at: datetime
    device_info: str | None = None
    ip_address: str | None = None
    is_current: bool = False

    model_config = ConfigDict(from_attributes=True)


class SessionListResponse(BaseModel):
    sessions: list[SessionInfo]
    total_sessions: int


class TokenData(BaseModel):
    email: str | None = None


# OAuth schemas
class OAuthLogin(BaseModel):
    provider: str  # 'google' or 'apple'
    access_token: str

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate OAuth provider."""
        if v.lower() not in ["google", "apple"]:
            raise ValueError("Invalid")
        return v.lower()


class OAuthUserInfo(BaseModel):
    provider: str
    oauth_id: str
    email: str
    name: str | None = None
    picture: str | None = None


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


# Password change schemas
class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength."""
        is_valid, error_msg = validate_password(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


class PasswordChangeResponse(BaseModel):
    detail: str


class AccountDeletionStatusResponse(BaseModel):
    deletion_requested: bool
    deletion_confirmed: bool
    deletion_scheduled_for: datetime | None = None
    can_cancel: bool
    grace_period_days: int


class UserListResponse(PaginatedResponse[UserResponse]):
    """Paginated response for user list."""


class UserSearchResponse(BaseModel):
    """Enhanced response for user search with metadata."""

    users: list[UserResponse]
    total_count: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool
    search_applied: bool = False
    filters_applied: list[str] = Field(default_factory=list)
    sort_field: str | None = None
    sort_order: str = "asc"


class DeletedUserResponse(UserBase):
    """Response model for soft-deleted users."""

    id: uuid.UUID
    is_superuser: bool
    is_verified: bool
    created_at: datetime
    oauth_provider: str | None = None
    # Soft delete fields
    is_deleted: bool = True
    deleted_at: datetime
    deleted_by: uuid.UUID | None = None
    deletion_reason: str | None = None

    model_config = ConfigDict(from_attributes=True)


class SoftDeleteRequest(BaseModel):
    """Request model for soft deleting a user."""

    reason: str | None = Field(
        None,
        max_length=500,
        description="Optional reason for deletion",
    )


class SoftDeleteResponse(BaseModel):
    """Response model for soft delete operations."""

    message: str
    user_id: uuid.UUID
    deleted_at: datetime
    deleted_by: uuid.UUID | None = None
    reason: str | None = None


class RestoreUserResponse(BaseModel):
    """Response model for user restoration."""

    message: str
    user_id: uuid.UUID
    restored_at: datetime


class DeletedUserListResponse(PaginatedResponse[DeletedUserResponse]):
    """Paginated response for deleted user list."""


class DeletedUserSearchResponse(BaseModel):
    """Enhanced response for deleted user search with metadata."""

    users: list[DeletedUserResponse]
    total_count: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool
    filters_applied: list[str] = Field(default_factory=list)
    sort_field: str | None = None
    sort_order: str = "desc"


# API Key schemas
class APIKeyBase(BaseModel):
    label: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable label for the API key",
    )
    scopes: list[str] = Field(
        default_factory=list,
        description="List of scopes the key has access to",
    )
    expires_at: datetime | None = Field(
        None,
        description="Optional expiration date for the key",
    )

    @field_validator("label")
    @classmethod
    def validate_label(cls, v: str) -> str:
        """Sanitize and validate label."""
        return sanitize_input(v, max_length=255)

    @field_validator("scopes")
    @classmethod
    def validate_scopes(cls, v: list[str]) -> list[str]:
        """Validate scopes are non-empty strings."""
        if not isinstance(v, list):
            raise ScopesTypeError

        validated_scopes = []
        for scope in v:
            if not isinstance(scope, str) or not scope.strip():
                raise InvalidScopeError
            validated_scopes.append(scope.strip())

        return validated_scopes


class APIKeyCreate(APIKeyBase):
    """Schema for creating an API key."""

    model_config = ConfigDict(from_attributes=True)

    @field_validator("expires_at")
    @classmethod
    def validate_expires_at(cls, v: datetime | None) -> datetime | None:
        """Validate that expiration date is in the future."""
        if v is not None:
            from app.utils.datetime_utils import utc_now

            if v <= utc_now():
                # Keep message short; allow inline exception here
                raise ValueError("Expiration must be in the future")  # noqa: TRY003
        return v


class APIKeyResponse(BaseModel):
    """Schema for API key responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    label: str
    scopes: list[str]
    user_id: uuid.UUID
    is_active: bool
    created_at: datetime
    expires_at: datetime | None = None

    @field_serializer("id", "user_id")
    def serialize_uuid(self, uuid_value: uuid.UUID, _info: SerializationInfo) -> str:
        return str(uuid_value)


class APIKeyCreateResponse(BaseModel):
    """Response model for newly created API key (includes the raw key once)."""

    api_key: APIKeyResponse
    raw_key: str = Field(
        ...,
        description="The raw API key (only returned once upon creation)",
    )


class APIKeyRotateResponse(BaseModel):
    """Response model for API key rotation."""

    api_key: APIKeyResponse
    new_raw_key: str = Field(
        ...,
        description="The new raw API key (only returned once upon rotation)",
    )


class APIKeyListResponse(PaginatedResponse[APIKeyResponse]):
    """Paginated response for API key list."""


class APIKeyUser(BaseModel):
    """Schema for API key user information."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scopes: list[str]
    user_id: uuid.UUID | None = None
    key_id: uuid.UUID

    @field_serializer("id", "user_id", "key_id")
    def serialize_uuid(
        self,
        uuid_value: uuid.UUID | None,
        _info: SerializationInfo,
    ) -> str | None:
        return str(uuid_value) if uuid_value else None


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(None, min_length=3, max_length=30)
    password: str | None = Field(None, min_length=8, max_length=128)
    full_name: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    # Add any other fields relevant to your user model
