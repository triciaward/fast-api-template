"""
Improved AuditLog model with better indexing and constraints.
"""

import uuid
from typing import Any

from sqlalchemy import Boolean, Column, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSON, TIMESTAMP, UUID
from sqlalchemy.orm import relationship

from app.database.database import Base
from app.utils.datetime_utils import utc_now


class AuditLog(Base):
    """
    Audit log model for tracking user actions and system events.

    Provides comprehensive audit trail with proper indexing for performance.
    """
    __tablename__ = "audit_logs"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Audit log entry unique identifier",
    )

    # Timestamp with consistent timezone handling
    timestamp = Column(
        TIMESTAMP(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
        comment="When the event occurred",
    )

    # User reference with proper foreign key and indexing
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),  # SET NULL to preserve audit trail
        nullable=True,  # Nullable for anonymous/system events
        index=True,
        comment="User who performed the action (null for system events)",
    )

    # Event classification with length constraint
    event_type = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Type of event (e.g., 'login_success', 'password_change')",
    )

    # Network information
    ip_address = Column(
        String(45),  # IPv6 max length
        nullable=True,
        index=True,  # Indexed for security analysis
        comment="IP address of the client",
    )
    user_agent = Column(
        Text,
        nullable=True,
        comment="User agent string from the client",
    )

    # Event outcome
    success = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,  # Indexed for filtering failed events
        comment="Whether the event was successful",
    )

    # Additional metadata with JSONB for better performance
    context = Column(
        JSON,
        nullable=True,
        comment="Additional event metadata as JSON",
    )

    # Session tracking
    session_id = Column(
        String(255),
        nullable=True,
        index=True,
        comment="Session identifier for correlation",
    )

    # Relationships
    user = relationship("User", back_populates="audit_logs", foreign_keys=[user_id], lazy="select")

    # Performance-optimized indexes
    __table_args__ = (
        # Composite index for time-based queries
        Index("ix_audit_log_timestamp_user", "timestamp", "user_id"),
        # Composite index for event analysis
        Index("ix_audit_log_event_success", "event_type", "success", "timestamp"),
        # Composite index for security monitoring
        Index("ix_audit_log_ip_timestamp", "ip_address", "timestamp"),
        # Composite index for session analysis
        Index("ix_audit_log_session_timestamp", "session_id", "timestamp"),
        # Partial index for failed events (more efficient)
        Index(
            "ix_audit_log_failed_events",
            "timestamp", "event_type", "user_id",
            postgresql_where="success = false",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, event_type='{self.event_type}', "
            f"user_id={self.user_id}, timestamp={self.timestamp}, "
            f"success={self.success})>"
        )

    @property
    def is_security_event(self) -> bool:
        """Check if this is a security-related event."""
        security_events = {
            "login_success", "login_failed", "password_change",
            "password_reset", "account_locked", "permission_denied",
            "api_key_created", "api_key_deleted",
        }
        return self.event_type in security_events

    @property
    def is_anonymous(self) -> bool:
        """Check if this is an anonymous event."""
        return self.user_id is None

    def add_context(self, key: str, value: Any) -> None:
        """Add context information to the audit log."""
        if self.context is None:
            self.context = {}
        self.context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get context information from the audit log."""
        if self.context is None:
            return default
        return self.context.get(key, default)
