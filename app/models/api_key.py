import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from app.database.database import Base
from app.models.base import SoftDeleteMixin


def utc_now() -> datetime:
    """Get current UTC datetime (replaces deprecated datetime.utcnow())."""
    return datetime.now(timezone.utc)


class APIKey(Base, SoftDeleteMixin):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True,
    )  # Nullable for system-level keys
    key_hash = Column(String(255), nullable=False, index=True, unique=True)
    label = Column(String(255), nullable=False)
    scopes = Column(JSON, nullable=False, default=list)  # List of strings
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    def __repr__(self) -> str:
        return f"<APIKey(id={self.id}, user_id={self.user_id}, label={self.label}, is_active={self.is_active}, expires_at={self.expires_at}, is_deleted={self.is_deleted})>"
