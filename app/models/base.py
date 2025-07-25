import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID


class SoftDeleteMixin:
    """Mixin to add soft delete functionality to models."""

    # Soft delete fields
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True, index=True)
    deleted_by = Column(
        UUID(as_uuid=True), nullable=True, index=True
    )  # User who deleted the record
    # Optional reason for deletion
    deletion_reason = Column(String(500), nullable=True)

    def soft_delete(self, deleted_by: uuid.UUID = None, reason: str = None) -> None:
        """Mark the record as deleted without actually removing it."""
        self.is_deleted = True  # type: ignore
        self.deleted_at = datetime.utcnow()  # type: ignore
        self.deleted_by = deleted_by  # type: ignore
        self.deletion_reason = reason  # type: ignore

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False  # type: ignore
        self.deleted_at = None  # type: ignore
        self.deleted_by = None  # type: ignore
        self.deletion_reason = None  # type: ignore

    @classmethod
    def get_active_query(cls):
        """Get a query that excludes soft-deleted records."""
        from sqlalchemy import select

        return select(cls).filter(cls.is_deleted.is_(False))

    @classmethod
    def get_deleted_query(cls):
        """Get a query that includes only soft-deleted records."""
        from sqlalchemy import select

        return select(cls).filter(cls.is_deleted.is_(True))

    @classmethod
    def get_all_query(cls):
        """Get a query that includes all records (active and deleted)."""
        from sqlalchemy import select

        return select(cls)
