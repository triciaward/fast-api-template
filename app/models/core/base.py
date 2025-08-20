"""
Improved base model with better practices.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, TypeVar

from sqlalchemy import Boolean, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column

from app.utils.datetime_utils import utc_now

if TYPE_CHECKING:
    from sqlalchemy.sql import Select

TModel = TypeVar("TModel", bound="SoftDeleteMixin")


@declarative_mixin
class SoftDeleteMixin:
    """
    Mixin to add soft delete functionality to models.

    Provides soft delete capabilities with audit trail.
    """

    # Soft delete fields with proper indexing
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        index=True,
    )
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),  # SET NULL to preserve audit trail
        nullable=True,
        index=True,
        comment="User who deleted the record",
    )
    deletion_reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Optional reason for deletion",
    )

    # Composite index for efficient soft delete queries
    __table_args__: tuple[Index, ...] = (
        Index("ix_soft_delete_composite", "is_deleted", "deleted_at"),
    )

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
        self.is_deleted = True
        self.deleted_at = utc_now()
        self.deleted_by = deleted_by
        self.deletion_reason = reason

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.deletion_reason = None

    @property
    def is_active(self) -> bool:
        """Check if the record is active (not soft-deleted)."""
        return bool(not self.is_deleted)

    @classmethod
    def get_active_query(cls: type[TModel]) -> "Select[tuple[TModel]]":
        """Get a query that excludes soft-deleted records."""
        from sqlalchemy import select

        return select(cls).filter(cls.is_deleted.is_(False))

    @classmethod
    def get_deleted_query(cls: type[TModel]) -> "Select[tuple[TModel]]":
        """Get a query that includes only soft-deleted records."""
        from sqlalchemy import select

        return select(cls).filter(cls.is_deleted.is_(True))

    @classmethod
    def get_all_query(cls: type[TModel]) -> "Select[tuple[TModel]]":
        """Get a query that includes all records (active and deleted)."""
        from sqlalchemy import select

        return select(cls)


@declarative_mixin
class TimestampMixin:
    """Mixin to add created/updated timestamps to models."""

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
        comment="Record creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
        index=True,
        comment="Record last update timestamp",
    )
