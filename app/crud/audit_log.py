from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models import AuditLog

# Type alias for both sync and async sessions
DBSession = AsyncSession | Session


def utc_now() -> datetime:
    """Get current UTC datetime (replaces deprecated datetime.utcnow())."""
    return datetime.now(UTC)


async def create_audit_log(
    db: DBSession,
    event_type: str,
    user_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    success: bool = True,
    context: dict[str, Any] | None = None,
    session_id: str | None = None,
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


def create_audit_log_sync(
    db: Session,
    event_type: str,
    user_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    success: bool = True,
    context: dict[str, Any] | None = None,
    session_id: str | None = None,
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


async def get_audit_logs_by_user(
    db: DBSession,
    user_id: str | None,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLog]:
    """Get audit logs for a specific user."""
    if isinstance(db, AsyncSession):
        result = await db.execute(
            select(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(desc(AuditLog.timestamp))
            .offset(offset)
            .limit(limit)
        )
    else:
        result = db.execute(
            select(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(desc(AuditLog.timestamp))
            .offset(offset)
            .limit(limit)
        )

    return result.scalars().all()


def get_audit_logs_by_user_sync(
    db: Session,
    user_id: str | None,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLog]:
    """Get audit logs for a specific user (sync version)."""
    # Handle empty string case for anonymous users
    if user_id == "":
        result = db.execute(
            select(AuditLog)
            .filter(AuditLog.user_id.is_(None))
            .order_by(desc(AuditLog.timestamp))
            .offset(offset)
            .limit(limit)
        )
    else:
        result = db.execute(
            select(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(desc(AuditLog.timestamp))
            .offset(offset)
            .limit(limit)
        )
    return result.scalars().all()


async def get_audit_logs_by_event_type(
    db: DBSession,
    event_type: str,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLog]:
    """Get audit logs by event type."""
    if isinstance(db, AsyncSession):
        result = await db.execute(
            select(AuditLog)
            .filter(AuditLog.event_type == event_type)
            .order_by(desc(AuditLog.timestamp))
            .offset(offset)
            .limit(limit)
        )
    else:
        result = db.execute(
            select(AuditLog)
            .filter(AuditLog.event_type == event_type)
            .order_by(desc(AuditLog.timestamp))
            .offset(offset)
            .limit(limit)
        )

    return result.scalars().all()


async def get_audit_logs_by_session(
    db: DBSession,
    session_id: str,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLog]:
    """Get audit logs for a specific session."""
    if isinstance(db, AsyncSession):
        result = await db.execute(
            select(AuditLog)
            .filter(AuditLog.session_id == session_id)
            .order_by(desc(AuditLog.timestamp))
            .offset(offset)
            .limit(limit)
        )
    else:
        result = db.execute(
            select(AuditLog)
            .filter(AuditLog.session_id == session_id)
            .order_by(desc(AuditLog.timestamp))
            .offset(offset)
            .limit(limit)
        )

    return result.scalars().all()


async def get_recent_audit_logs(
    db: DBSession,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLog]:
    """Get recent audit logs."""
    if isinstance(db, AsyncSession):
        result = await db.execute(
            select(AuditLog)
            .order_by(desc(AuditLog.timestamp))
            .offset(offset)
            .limit(limit)
        )
    else:
        result = db.execute(
            select(AuditLog)
            .order_by(desc(AuditLog.timestamp))
            .offset(offset)
            .limit(limit)
        )

    return result.scalars().all()


async def get_failed_audit_logs(
    db: DBSession,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLog]:
    """Get failed audit logs."""
    if isinstance(db, AsyncSession):
        result = await db.execute(
            select(AuditLog)
            .filter(AuditLog.success.is_(False))
            .order_by(desc(AuditLog.timestamp))
            .offset(offset)
            .limit(limit)
        )
    else:
        result = db.execute(
            select(AuditLog)
            .filter(AuditLog.success.is_(False))
            .order_by(desc(AuditLog.timestamp))
            .offset(offset)
            .limit(limit)
        )

    return result.scalars().all()


async def cleanup_old_audit_logs(db: DBSession, days_to_keep: int = 90) -> int:
    """Clean up old audit logs."""
    cutoff_date = utc_now() - timedelta(days=days_to_keep)

    if isinstance(db, AsyncSession):
        result = await db.execute(
            select(AuditLog).filter(AuditLog.timestamp < cutoff_date)
        )
        old_logs = result.scalars().all()
    else:
        result = db.execute(select(AuditLog).filter(AuditLog.timestamp < cutoff_date))
        old_logs = result.scalars().all()

    count = 0
    for log in old_logs:
        if isinstance(db, AsyncSession):
            await db.delete(log)
        else:
            db.delete(log)
        count += 1

    if isinstance(db, AsyncSession):
        await db.commit()
    else:
        db.commit()

    return count
