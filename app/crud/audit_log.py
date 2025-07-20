from datetime import datetime
from typing import Any, Optional, Union

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.models import AuditLog

# Type alias for both sync and async sessions
DBSession = Union[AsyncSession, Session]


async def create_audit_log(
    db: DBSession,
    event_type: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    success: bool = True,
    context: Optional[dict[str, Any]] = None,
    session_id: Optional[str] = None,
) -> AuditLog:
    """Create a new audit log entry."""
    audit_log = AuditLog(
        event_type=event_type,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
        context=context,
        session_id=session_id,
    )
    db.add(audit_log)
    if isinstance(db, AsyncSession):
        await db.commit()
        try:
            await db.refresh(audit_log)
        except Exception:
            pass
    else:
        db.commit()
        try:
            db.refresh(audit_log)
        except Exception:
            pass
    return audit_log


async def get_audit_logs_by_user(
    db: DBSession,
    user_id: Optional[str],
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLog]:
    """Get audit logs for a specific user, ordered by timestamp descending."""
    if isinstance(db, AsyncSession):
        if user_id:
            result = await db.execute(
                select(AuditLog)
                .filter(AuditLog.user_id == user_id)
                .order_by(desc(AuditLog.timestamp))
                .limit(limit)
                .offset(offset)
            )
        else:
            # Handle anonymous logs (user_id is None or empty)
            result = await db.execute(
                select(AuditLog)
                .filter(AuditLog.user_id.is_(None))
                .order_by(desc(AuditLog.timestamp))
                .limit(limit)
                .offset(offset)
            )
    else:
        if user_id:
            result = db.execute(
                select(AuditLog)
                .filter(AuditLog.user_id == user_id)
                .order_by(desc(AuditLog.timestamp))
                .limit(limit)
                .offset(offset)
            )
        else:
            # Handle anonymous logs (user_id is None or empty)
            result = db.execute(
                select(AuditLog)
                .filter(AuditLog.user_id.is_(None))
                .order_by(desc(AuditLog.timestamp))
                .limit(limit)
                .offset(offset)
            )
    return list(result.scalars().all())


async def get_audit_logs_by_event_type(
    db: DBSession,
    event_type: str,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLog]:
    """Get audit logs for a specific event type, ordered by timestamp descending."""
    if isinstance(db, AsyncSession):
        result = await db.execute(
            select(AuditLog)
            .filter(AuditLog.event_type == event_type)
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
            .offset(offset)
        )
    else:
        result = db.execute(
            select(AuditLog)
            .filter(AuditLog.event_type == event_type)
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
            .offset(offset)
        )
    return list(result.scalars().all())


async def get_audit_logs_by_date_range(
    db: DBSession,
    start_date: datetime,
    end_date: datetime,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLog]:
    """Get audit logs within a date range, ordered by timestamp descending."""
    if isinstance(db, AsyncSession):
        result = await db.execute(
            select(AuditLog)
            .filter(AuditLog.timestamp >= start_date)
            .filter(AuditLog.timestamp <= end_date)
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
            .offset(offset)
        )
    else:
        result = db.execute(
            select(AuditLog)
            .filter(AuditLog.timestamp >= start_date)
            .filter(AuditLog.timestamp <= end_date)
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
            .offset(offset)
        )
    return list(result.scalars().all())


async def get_failed_login_attempts(
    db: DBSession,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    since: Optional[datetime] = None,
) -> list[AuditLog]:
    """Get failed login attempts, optionally filtered by user, IP, or time."""
    query = select(AuditLog).filter(
        AuditLog.event_type == "login_failed",
        ~AuditLog.success
    )
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if ip_address:
        query = query.filter(AuditLog.ip_address == ip_address)
    if since:
        query = query.filter(AuditLog.timestamp >= since)
    query = query.order_by(desc(AuditLog.timestamp))
    if isinstance(db, AsyncSession):
        result = await db.execute(query)
    else:
        result = db.execute(query)
    return list(result.scalars().all())


async def get_audit_log_by_id(db: DBSession, log_id: str) -> Optional[AuditLog]:
    """Get a specific audit log by ID."""
    if isinstance(db, AsyncSession):
        result = await db.execute(select(AuditLog).filter(AuditLog.id == log_id))
    else:
        result = db.execute(select(AuditLog).filter(AuditLog.id == log_id))
    return result.scalar_one_or_none()


# Sync versions for TestClient compatibility
def create_audit_log_sync(
    db: Session,
    event_type: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    success: bool = True,
    context: Optional[dict[str, Any]] = None,
    session_id: Optional[str] = None,
) -> AuditLog:
    """Create a new audit log entry (sync version)."""
    audit_log = AuditLog(
        event_type=event_type,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
        context=context,
        session_id=session_id,
    )
    db.add(audit_log)
    db.commit()
    try:
        db.refresh(audit_log)
    except Exception:
        pass
    return audit_log


def get_audit_logs_by_user_sync(
    db: Session,
    user_id: Optional[str],
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLog]:
    """Get audit logs for a specific user (sync version)."""
    if user_id:
        result = db.execute(
            select(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
            .offset(offset)
        )
    else:
        # Handle anonymous logs (user_id is None or empty)
        result = db.execute(
            select(AuditLog)
            .filter(AuditLog.user_id.is_(None))
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
            .offset(offset)
        )
    return list(result.scalars().all())


def get_failed_login_attempts_sync(
    db: Session,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    since: Optional[datetime] = None,
) -> list[AuditLog]:
    """Get failed login attempts (sync version)."""
    query = select(AuditLog).filter(
        AuditLog.event_type == "login_failed",
        ~AuditLog.success
    )
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if ip_address:
        query = query.filter(AuditLog.ip_address == ip_address)
    if since:
        query = query.filter(AuditLog.timestamp >= since)
    query = query.order_by(desc(AuditLog.timestamp))
    result = db.execute(query)
    return list(result.scalars().all())
