import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database.database import Base


def utc_now() -> datetime:
    """Get current UTC datetime (replaces deprecated datetime.utcnow())."""
    return datetime.now(UTC)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)
    user_id = Column(
        UUID(as_uuid=True), nullable=True, index=True
    )  # Nullable for anonymous events
    # e.g., 'login_success', 'password_change'
    event_type = Column(String(100), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    success = Column(Boolean, nullable=False, default=True)
    context = Column(JSON, nullable=True)  # Flexible metadata storage
    session_id = Column(String(255), nullable=True, index=True)

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, event_type={self.event_type}, user_id={self.user_id}, timestamp={self.timestamp}, success={self.success})>"
