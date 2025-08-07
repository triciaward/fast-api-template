"""Authentication and user management schemas."""

from .user import (
    AccountDeletionCancelRequest,
    AccountDeletionCancelResponse,
    AccountDeletionConfirmRequest,
    AccountDeletionConfirmResponse,
    # Account deletion schemas
    AccountDeletionRequest,
    AccountDeletionResponse,
    AccountDeletionStatusResponse,
    # API Key schemas
    APIKeyBase,
    APIKeyCreate,
    APIKeyCreateResponse,
    APIKeyListResponse,
    APIKeyResponse,
    APIKeyRotateResponse,
    APIKeyUser,
    DeletedUserListResponse,
    DeletedUserResponse,
    DeletedUserSearchResponse,
    # Email verification schemas
    EmailVerificationRequest,
    EmailVerificationResponse,
    InvalidScopeError,
    # OAuth schemas
    OAuthLogin,
    OAuthUserInfo,
    PasswordChangeRequest,
    PasswordChangeResponse,
    PasswordResetConfirmRequest,
    PasswordResetConfirmResponse,
    # Password management schemas
    PasswordResetRequest,
    PasswordResetResponse,
    RefreshTokenResponse,
    RestoreUserResponse,
    # Custom exceptions
    ScopesTypeError,
    SessionInfo,
    SessionListResponse,
    # Soft delete schemas
    SoftDeleteRequest,
    SoftDeleteResponse,
    # Token/Session schemas
    Token,
    TokenData,
    # Base schemas
    UserBase,
    UserCreate,
    UserListResponse,
    UserLogin,
    UserResponse,
    UserSearchResponse,
    UserUpdate,
    VerifyEmailRequest,
    VerifyEmailResponse,
)

__all__ = [
    # Base schemas
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserUpdate",
    "UserListResponse",
    "UserSearchResponse",

    # Token/Session schemas
    "Token",
    "TokenData",
    "RefreshTokenResponse",
    "SessionInfo",
    "SessionListResponse",

    # OAuth schemas
    "OAuthLogin",
    "OAuthUserInfo",

    # Email verification schemas
    "EmailVerificationRequest",
    "EmailVerificationResponse",
    "VerifyEmailRequest",
    "VerifyEmailResponse",

    # Password management schemas
    "PasswordResetRequest",
    "PasswordResetResponse",
    "PasswordResetConfirmRequest",
    "PasswordResetConfirmResponse",
    "PasswordChangeRequest",
    "PasswordChangeResponse",

    # Account deletion schemas
    "AccountDeletionRequest",
    "AccountDeletionResponse",
    "AccountDeletionConfirmRequest",
    "AccountDeletionConfirmResponse",
    "AccountDeletionCancelRequest",
    "AccountDeletionCancelResponse",
    "AccountDeletionStatusResponse",
    "DeletedUserResponse",

    # Soft delete schemas
    "SoftDeleteRequest",
    "SoftDeleteResponse",
    "RestoreUserResponse",
    "DeletedUserListResponse",
    "DeletedUserSearchResponse",

    # API Key schemas
    "APIKeyBase",
    "APIKeyCreate",
    "APIKeyResponse",
    "APIKeyCreateResponse",
    "APIKeyRotateResponse",
    "APIKeyListResponse",
    "APIKeyUser",

    # Custom exceptions
    "ScopesTypeError",
    "InvalidScopeError",
]
