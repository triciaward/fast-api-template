"""
Improved APIKey model with better constraints and indexing.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="API key unique identifier",
    )

    # User reference (nullable for system-level keys)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="User who owns this API key (null for system keys)",
    )

    # Key information with proper constraints
    key_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        unique=True,
        comment="Hashed API key value",
    )

    # Deterministic fingerprint for efficient lookup before bcrypt verify
    key_fingerprint: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="Deterministic fingerprint (SHA-256) of API key for lookup",
    )
    label: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Human-readable label for the API key",
    )

    # Scopes with proper JSON handling
    scopes: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        comment="List of permission scopes for this key",
    )

    # Status and expiration
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether the API key is active",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        index=True,
        comment="When the API key expires (null for no expiration)",
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="api_keys",
        foreign_keys=[user_id],
        lazy="select",
    )

    # Performance-optimized indexes
    __table_args__: tuple[Index, ...] = (
        # Composite index for user's active keys
        Index("ix_api_key_user_active", "user_id", "is_active", "expires_at"),
        # Composite index for system keys
        Index("ix_api_key_system", "is_active", "expires_at"),
        # GIN index for JSONB scopes lookups
        Index("ix_api_key_scopes", "scopes", postgresql_using="gin"),
        # Fingerprint index for verification shortcuts
        Index("ix_api_key_fingerprint", "key_fingerprint"),
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
        return bool(self.expires_at < utc_now())

    @property
    def is_valid(self) -> bool:
        """Check if the API key is valid (active and not expired)."""
        return bool(self.is_active and not self.is_expired and not self.is_deleted)

    def has_scope(self, scope: str) -> bool:
        """Check if the API key has a specific scope."""
        scopes = list(self.scopes or [])
        if not scopes:
            return False
        return scope in scopes

    def has_any_scope(self, scopes: list[str]) -> bool:
        """Check if the API key has any of the specified scopes."""
        current = list(self.scopes or [])
        if not current:
            return False
        return any(scope in current for scope in scopes)

    def has_all_scopes(self, scopes: list[str]) -> bool:
        """Check if the API key has all of the specified scopes."""
        current = list(self.scopes or [])
        if not current:
            return False
        return all(scope in current for scope in scopes)

    @property
    def is_system_key(self) -> bool:
        """Check if this is a system-level API key."""
        return bool(self.user_id is None)

    def revoke(self) -> None:
        """Revoke the API key."""
        self.is_active = False
        self.updated_at = utc_now()


if TYPE_CHECKING:
    from app.models.auth.user import User
