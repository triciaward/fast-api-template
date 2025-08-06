"""
Admin-specific Pydantic schemas.

This module provides admin-only schemas for user management and admin operations.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.utils.pagination import PaginatedResponse


class AdminUserCreate(BaseModel):
    """Schema for creating users via admin interface."""

    email: str = Field(..., description="User's email address")
    username: str = Field(..., description="User's username")
    password: str = Field(..., description="User's password")
    is_superuser: bool = Field(default=False, description="Whether user is a superuser")
    is_verified: bool = Field(default=False, description="Whether user is verified")


class AdminUserUpdate(BaseModel):
    """Schema for updating users via admin interface."""

    email: str | None = Field(None, description="User's email address")
    username: str | None = Field(None, description="User's username")
    password: str | None = Field(None, description="User's password")
    is_superuser: bool | None = Field(None, description="Whether user is a superuser")
    is_verified: bool | None = Field(None, description="Whether user is verified")


class AdminUserResponse(BaseModel):
    """Schema for user responses in admin interface."""

    id: UUID = Field(..., description="User's unique identifier")
    email: str = Field(..., description="User's email address")
    username: str = Field(..., description="User's username")
    is_superuser: bool = Field(..., description="Whether user is a superuser")
    is_verified: bool = Field(..., description="Whether user is verified")
    is_deleted: bool = Field(..., description="Whether user is deleted")
    date_created: datetime = Field(..., description="When user was created")
    oauth_provider: str | None = Field(None, description="OAuth provider if applicable")
    oauth_id: str | None = Field(None, description="OAuth provider's user ID")
    oauth_email: str | None = Field(None, description="Email from OAuth provider")
    deletion_requested_at: datetime | None = Field(
        None, description="When deletion was requested",
    )
    deletion_confirmed_at: datetime | None = Field(
        None, description="When deletion was confirmed",
    )
    deletion_scheduled_for: datetime | None = Field(
        None, description="When user will be deleted",
    )

    model_config = ConfigDict(from_attributes=True)


class AdminUserListResponse(PaginatedResponse[AdminUserResponse]):
    """Schema for paginated user list responses using the generic pagination system."""


class AdminUserFilters(BaseModel):
    """Schema for filtering users in admin interface."""

    is_superuser: bool | None = Field(None, description="Filter by superuser status")
    is_verified: bool | None = Field(None, description="Filter by verification status")
    is_deleted: bool | None = Field(None, description="Filter by deletion status")
    oauth_provider: str | None = Field(None, description="Filter by OAuth provider")


class AdminUserStatistics(BaseModel):
    """Schema for user statistics in admin dashboard."""

    total_users: int = Field(..., description="Total number of users")
    superusers: int = Field(..., description="Number of superusers")
    verified_users: int = Field(..., description="Number of verified users")
    oauth_users: int = Field(..., description="Number of OAuth users")
    deleted_users: int = Field(..., description="Number of deleted users")
    regular_users: int = Field(..., description="Number of regular users")
    unverified_users: int = Field(..., description="Number of unverified users")


class AdminUserToggleResponse(BaseModel):
    """Schema for toggle operation responses."""

    user_id: UUID = Field(..., description="User's unique identifier")
    field: str = Field(..., description="Field that was toggled")
    new_value: bool = Field(..., description="New value after toggle")
    message: str = Field(..., description="Success message")


class AdminBulkOperationRequest(BaseModel):
    """Schema for bulk operations on users."""

    user_ids: list[UUID] = Field(..., description="List of user IDs to operate on")
    operation: str = Field(
        ..., description="Operation to perform (delete, verify, etc.)",
    )


class AdminBulkOperationResponse(BaseModel):
    """Schema for bulk operation responses."""

    operation: str = Field(..., description="Operation that was performed")
    total_users: int = Field(..., description="Total number of users processed")
    successful: int = Field(..., description="Number of successful operations")
    failed: int = Field(..., description="Number of failed operations")
    failed_user_ids: list[UUID] = Field(default=[], description="User IDs that failed")


class AdminSessionInfo(BaseModel):
    """Schema for session information in admin interface."""

    session_id: str = Field(..., description="Session identifier")
    user_id: UUID = Field(..., description="User ID")
    user_email: str = Field(..., description="User email")
    created_at: datetime = Field(..., description="When session was created")
    expires_at: datetime = Field(..., description="When session expires")
    device_info: str | None = Field(None, description="Device information")
    ip_address: str | None = Field(None, description="IP address")


class AdminSessionListResponse(BaseModel):
    """Schema for session list responses."""

    sessions: list[AdminSessionInfo] = Field(..., description="List of sessions")
    total: int = Field(..., description="Total number of sessions")


class AdminSystemInfo(BaseModel):
    """Schema for system information in admin dashboard."""

    total_users: int = Field(..., description="Total number of users")
    active_sessions: int = Field(..., description="Number of active sessions")
    system_uptime: str = Field(..., description="System uptime")
    database_size: str | None = Field(None, description="Database size")
    last_backup: datetime | None = Field(None, description="Last backup time")
