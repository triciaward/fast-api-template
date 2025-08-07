"""
Improved User model with better practices and constraints.
"""

import uuid

from sqlalchemy import Boolean, Column, Index, String
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import relationship

from app.database.database import Base
from app.models.core.base import SoftDeleteMixin, TimestampMixin


class User(Base, SoftDeleteMixin, TimestampMixin):
    """
    User model with improved constraints and indexing.

    Supports both regular authentication and OAuth.
    """

    __tablename__ = "users"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="User's unique identifier",
    )

    # Core user information with proper constraints
    email = Column(
        String(254),  # RFC 5321 email length limit
        unique=True,
        index=True,
        nullable=False,
        comment="User's email address",
    )
    username = Column(
        String(50),  # Reasonable username limit
        unique=True,
        index=True,
        nullable=False,
        comment="User's unique username",
    )
    hashed_password = Column(
        String(255),  # Explicit length for password hash
        nullable=True,  # Nullable for OAuth users
        comment="Hashed password (null for OAuth users)",
    )

    # User status flags
    is_superuser = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,  # Indexed for admin queries
        comment="Whether user has superuser privileges",
    )
    is_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,  # Indexed for filtering verified users
        comment="Whether user's email is verified",
    )

    # OAuth fields with proper indexing
    oauth_provider = Column(
        String(20),  # 'google', 'apple', etc.
        nullable=True,
        comment="OAuth provider name",
    )
    oauth_id = Column(
        String(255),  # OAuth provider's user ID
        nullable=True,
        comment="OAuth provider's user identifier",
    )
    oauth_email = Column(
        String(254),  # Same as email constraint
        nullable=True,
        comment="Email address from OAuth provider",
    )

    # Email verification with proper token length
    verification_token = Column(
        String(255),
        nullable=True,
        unique=True,  # Ensure token uniqueness
        comment="Token for email verification",
    )
    verification_token_expires = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="Expiration time for verification token",
    )

    # Password reset with proper token length
    password_reset_token = Column(
        String(255),
        nullable=True,
        unique=True,  # Ensure token uniqueness
        comment="Token for password reset",
    )
    password_reset_token_expires = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="Expiration time for password reset token",
    )

    # Account deletion (GDPR compliance)
    deletion_requested_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="When account deletion was requested",
    )
    deletion_confirmed_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="When account deletion was confirmed",
    )
    deletion_scheduled_for = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="When account deletion is scheduled",
    )
    deletion_token = Column(
        String(255),
        nullable=True,
        unique=True,  # Ensure token uniqueness
        comment="Token for account deletion confirmation",
    )
    deletion_token_expires = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="Expiration time for deletion token",
    )

    # Relationships (lazy loading for better performance)
    api_keys = relationship(
        "APIKey", back_populates="user", foreign_keys="APIKey.user_id", lazy="select",
    )
    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        foreign_keys="RefreshToken.user_id",
        lazy="select",
    )
    audit_logs = relationship(
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
        return self.oauth_provider is not None and self.oauth_id is not None

    @property
    def has_password(self) -> bool:
        """Check if user has a password set."""
        return self.hashed_password is not None

    def can_login_with_password(self) -> bool:
        """Check if user can login with password."""
        return self.has_password and self.is_verified and not self.is_deleted

    def get_display_name(self) -> str:
        """Get a display name for the user."""
        return self.username or self.email.split("@")[0]
