"""
Improved base model with better practices.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import declarative_mixin

from app.utils.datetime_utils import utc_now

if TYPE_CHECKING:
    from sqlalchemy.sql import Select


@declarative_mixin
class SoftDeleteMixin:
    """
    Mixin to add soft delete functionality to models.

    Provides soft delete capabilities with audit trail.
    """

    # Soft delete fields with proper indexing
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True, index=True)
    deleted_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),  # SET NULL to preserve audit trail
        nullable=True,
        index=True,
        comment="User who deleted the record",
    )
    deletion_reason = Column(
        String(500),
        nullable=True,
        comment="Optional reason for deletion",
    )

    # Composite index for efficient soft delete queries
    __table_args__ = (Index("ix_soft_delete_composite", "is_deleted", "deleted_at"),)

    def soft_delete(
        self,
        deleted_by: uuid.UUID | None = None,
        reason: str | None = None,
    ) -> None:
        """
        Mark the record as deleted without actually removing it.

        Args:
            deleted_by: UUID of the user performing the deletion
            reason: Optional reason for deletion
        """
        self.is_deleted = True  # type: ignore
        self.deleted_at = utc_now()  # type: ignore
        self.deleted_by = deleted_by  # type: ignore
        self.deletion_reason = reason  # type: ignore

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False  # type: ignore
        self.deleted_at = None  # type: ignore
        self.deleted_by = None  # type: ignore
        self.deletion_reason = None  # type: ignore

    @property
    def is_active(self) -> bool:
        """Check if the record is active (not soft-deleted)."""
        return not self.is_deleted  # type: ignore

    @classmethod
    def get_active_query(cls) -> "Select":
        """Get a query that excludes soft-deleted records."""
        from sqlalchemy import select

        return select(cls).filter(cls.is_deleted.is_(False))

    @classmethod
    def get_deleted_query(cls) -> "Select":
        """Get a query that includes only soft-deleted records."""
        from sqlalchemy import select

        return select(cls).filter(cls.is_deleted.is_(True))

    @classmethod
    def get_all_query(cls) -> "Select":
        """Get a query that includes all records (active and deleted)."""
        from sqlalchemy import select

        return select(cls)


@declarative_mixin
class TimestampMixin:
    """Mixin to add created/updated timestamps to models."""

    created_at = Column(
        TIMESTAMP(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
        comment="Record creation timestamp",
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
        index=True,
        comment="Record last update timestamp",
    )
