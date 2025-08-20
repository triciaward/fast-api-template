"""
Improved User model with better practices and constraints.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Index, String
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
from app.models.core.base import SoftDeleteMixin, TimestampMixin


class User(Base, SoftDeleteMixin, TimestampMixin):
    """
    User model with improved constraints and indexing.

    Supports both regular authentication and OAuth.
    """

    __tablename__ = "users"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="User's unique identifier",
    )

    # Core user information with proper constraints
    email: Mapped[str] = mapped_column(
        String(254),
        unique=True,
        index=True,
        nullable=False,
        comment="User's email address",
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment="User's unique username",
    )
    hashed_password: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Hashed password (null for OAuth users)",
    )

    # User status flags
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether user has superuser privileges",
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether user's email is verified",
    )

    # OAuth fields with proper indexing
    oauth_provider: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="OAuth provider name",
    )
    oauth_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="OAuth provider's user identifier",
    )
    oauth_email: Mapped[str | None] = mapped_column(
        String(254),
        nullable=True,
        comment="Email address from OAuth provider",
    )

    # Email verification with proper token length
    verification_token: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        comment="Token for email verification",
    )
    verification_token_expires: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="Expiration time for verification token",
    )

    # Password reset with proper token length
    password_reset_token: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        comment="Token for password reset",
    )
    password_reset_token_expires: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="Expiration time for password reset token",
    )

    # Account deletion (GDPR compliance)
    deletion_requested_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="When account deletion was requested",
    )
    deletion_confirmed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="When account deletion was confirmed",
    )
    deletion_scheduled_for: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="When account deletion is scheduled",
    )
    deletion_token: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        comment="Token for account deletion confirmation",
    )
    deletion_token_expires: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="Expiration time for deletion token",
    )

    # Relationships (lazy loading for better performance)
    api_keys: Mapped[list["APIKey"]] = relationship(
        "APIKey",
        back_populates="user",
        foreign_keys="APIKey.user_id",
        lazy="select",
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        foreign_keys="RefreshToken.user_id",
        lazy="select",
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
        foreign_keys="AuditLog.user_id",
        lazy="select",
    )

    # Improved table constraints and indexes
    __table_args__ = (
        # Composite index for OAuth lookups
        Index("ix_user_oauth_provider_id", "oauth_provider", "oauth_id"),
        # Composite index for user status queries
        Index("ix_user_status", "is_deleted", "is_verified", "is_superuser"),
        # Unique constraint for OAuth users (partial unique index instead)
        Index(
            "uq_user_oauth",
            "oauth_provider",
            "oauth_id",
            unique=True,
            postgresql_where="oauth_provider IS NOT NULL AND oauth_id IS NOT NULL",
        ),
        # Index for token-based operations
        Index("ix_user_verification_token", "verification_token"),
        Index("ix_user_password_reset_token", "password_reset_token"),
        Index("ix_user_deletion_token", "deletion_token"),
    )

    def __repr__(self) -> str:
        return (
            f"<User(id={self.id}, email='{self.email}', username='{self.username}', "
            f"is_superuser={self.is_superuser}, is_verified={self.is_verified}, "
            f"is_deleted={self.is_deleted})>"
        )

    @property
    def is_oauth_user(self) -> bool:
        """Check if this is an OAuth user."""
        return bool(self.oauth_provider is not None and self.oauth_id is not None)

    @property
    def has_password(self) -> bool:
        """Check if user has a password set."""
        return bool(self.hashed_password is not None)

    def can_login_with_password(self) -> bool:
        """Check if user can login with password."""
        return bool(self.has_password and self.is_verified and not self.is_deleted)

    def get_display_name(self) -> str:
        """Get a display name for the user."""
        return str(self.username or self.email.split("@")[0])


if TYPE_CHECKING:
    # Only for typing to avoid import cycles
    from app.models.auth.api_key import APIKey
    from app.models.auth.refresh_token import RefreshToken
    from app.models.system.audit_log import AuditLog
