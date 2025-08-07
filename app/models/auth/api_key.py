"""
Improved APIKey model with better constraints and indexing.
"""

import uuid

from sqlalchemy import Boolean, Column, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSON, TIMESTAMP, UUID
from sqlalchemy.orm import relationship

from app.database.database import Base
from app.models.core.base import SoftDeleteMixin, TimestampMixin
from app.utils.datetime_utils import utc_now


class APIKey(Base, SoftDeleteMixin, TimestampMixin):
    """
    API Key model for secure API access.

    Supports both user-specific and system-level API keys.
    """

    __tablename__ = "api_keys"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="API key unique identifier",
    )

    # User reference (nullable for system-level keys)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,  # Nullable for system-level keys
        index=True,
        comment="User who owns this API key (null for system keys)",
    )

    # Key information with proper constraints
    key_hash = Column(
        String(255),
        nullable=False,
        index=True,
        unique=True,
        comment="Hashed API key value",
    )
    label = Column(
        String(255),
        nullable=False,
        comment="Human-readable label for the API key",
    )

    # Scopes with proper JSON handling
    scopes = Column(
        JSON,
        nullable=False,
        default=list,
        comment="List of permission scopes for this key",
    )

    # Status and expiration
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether the API key is active",
    )
    expires_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        index=True,
        comment="When the API key expires (null for no expiration)",
    )

    # Relationships
    user = relationship(
        "User", back_populates="api_keys", foreign_keys=[user_id], lazy="select",
    )

    # Performance-optimized indexes
    __table_args__ = (
        # Composite index for user's active keys
        Index("ix_api_key_user_active", "user_id", "is_active", "expires_at"),
        # Composite index for system keys
        Index("ix_api_key_system", "is_active", "expires_at"),
        # Index for scope-based queries
        Index("ix_api_key_scopes", "scopes"),
        # Partial index for expired keys
        Index(
            "ix_api_key_expired",
            "id",
            "is_active",
            postgresql_where="expires_at IS NOT NULL AND expires_at < NOW()",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<APIKey(id={self.id}, user_id={self.user_id}, "
            f"label='{self.label}', is_active={self.is_active}, "
            f"expires_at={self.expires_at}, is_deleted={self.is_deleted})>"
        )

    @property
    def is_expired(self) -> bool:
        """Check if the API key has expired."""
        if self.expires_at is None:
            return False
        return self.expires_at < utc_now()

    @property
    def is_valid(self) -> bool:
        """Check if the API key is valid (active and not expired)."""
        return self.is_active and not self.is_expired and not self.is_deleted

    def has_scope(self, scope: str) -> bool:
        """Check if the API key has a specific scope."""
        if not self.scopes:
            return False
        return scope in self.scopes

    def has_any_scope(self, scopes: list[str]) -> bool:
        """Check if the API key has any of the specified scopes."""
        if not self.scopes:
            return False
        return any(scope in self.scopes for scope in scopes)

    def has_all_scopes(self, scopes: list[str]) -> bool:
        """Check if the API key has all of the specified scopes."""
        if not self.scopes:
            return False
        return all(scope in self.scopes for scope in scopes)

    @property
    def is_system_key(self) -> bool:
        """Check if this is a system-level API key."""
        return self.user_id is None

    def revoke(self) -> None:
        """Revoke the API key."""
        self.is_active = False  # type: ignore
        self.updated_at = utc_now()  # type: ignore
