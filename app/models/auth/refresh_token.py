"""
Improved RefreshToken model with better constraints and indexing.
"""

import uuid

from sqlalchemy import Boolean, Column, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import relationship

from app.database.database import Base
from app.models.core.base import SoftDeleteMixin, TimestampMixin
from app.utils.datetime_utils import utc_now


class RefreshToken(Base, SoftDeleteMixin, TimestampMixin):
    """
    Refresh token model for secure session management.

    Provides secure token-based authentication with proper expiration handling.
    """

    __tablename__ = "refresh_tokens"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Refresh token unique identifier",
    )

    # User reference with proper foreign key
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who owns this refresh token",
    )

    # Token information with proper constraints
    token_hash = Column(
        String(255),
        nullable=False,
        index=True,
        unique=True,  # Ensure token uniqueness
        comment="Hashed refresh token value",
    )

    # Deterministic fingerprint for efficient lookup before bcrypt verify
    token_fingerprint = Column(
        String(64),
        nullable=True,
        index=True,
        comment="Deterministic fingerprint of the refresh token for lookup",
    )

    # Expiration with consistent timezone handling
    expires_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
        comment="When the refresh token expires",
    )

    # Status tracking
    is_revoked = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether the token has been revoked",
    )

    # Device and network information
    device_info = Column(
        Text,
        nullable=True,
        comment="Device information (browser, OS, etc.)",
    )
    ip_address = Column(
        String(45),  # IPv6 max length
        nullable=True,
        index=True,  # Indexed for security analysis
        comment="IP address where token was created",
    )

    # Relationships
    user = relationship(
        "User",
        back_populates="refresh_tokens",
        foreign_keys=[user_id],
        lazy="select",
    )

    # Performance-optimized indexes
    __table_args__ = (
        # Composite index for user's active tokens
        Index("ix_refresh_token_user_active", "user_id", "is_revoked", "expires_at"),
        # Composite index for token validation
        Index("ix_refresh_token_validation", "token_hash", "is_revoked", "expires_at"),
        # Index on fingerprint for quick candidate lookup
        Index("ix_refresh_token_fingerprint", "token_fingerprint"),
        # Index for security monitoring
        Index("ix_refresh_token_ip_timestamp", "ip_address", "created_at"),
        # Partial index for revoked tokens
        Index(
            "ix_refresh_token_revoked",
            "user_id",
            "created_at",
            postgresql_where="is_revoked = true",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<RefreshToken(id={self.id}, user_id={self.user_id}, "
            f"expires_at={self.expires_at}, is_revoked={self.is_revoked}, "
            f"is_deleted={self.is_deleted})>"
        )

    @property
    def is_expired(self) -> bool:
        """Check if the refresh token has expired."""
        return self.expires_at < utc_now()

    @property
    def is_valid(self) -> bool:
        """Check if the refresh token is valid (not revoked, not expired, not deleted)."""
        return not self.is_revoked and not self.is_expired and not self.is_deleted

    @property
    def is_active(self) -> bool:
        """Check if the refresh token is active (valid and not soft-deleted)."""
        return self.is_valid

    def revoke(self) -> None:
        """Revoke the refresh token."""
        self.is_revoked = True  # type: ignore
        self.updated_at = utc_now()  # type: ignore

    def get_device_summary(self) -> str:
        """Get a human-readable device summary."""
        if not self.device_info:
            return "Unknown device"

        # Simple parsing for common user agent patterns
        ua = self.device_info.lower()
        if "chrome" in ua:
            return "Chrome"
        if "firefox" in ua:
            return "Firefox"
        if "safari" in ua:
            return "Safari"
        if "edge" in ua:
            return "Edge"
        if "mobile" in ua or "android" in ua or "iphone" in ua:
            return "Mobile device"
        return "Other browser"

    @property
    def time_until_expiry(self) -> int | None:
        """Get seconds until token expires (negative if expired)."""
        if self.is_expired:
            return None
        delta = self.expires_at - utc_now()
        return int(delta.total_seconds())

    @property
    def is_near_expiry(self) -> bool:
        """Check if token expires within 24 hours."""
        if self.is_expired:
            return False
        delta = self.expires_at - utc_now()
        return delta.total_seconds() < 86400  # 24 hours
