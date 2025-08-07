from datetime import timedelta
from typing import Any, TypeAlias

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog
from app.utils.datetime_utils import utc_now

# Type alias for async sessions only
DBSession: TypeAlias = AsyncSession


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
    await db.commit()
    try:
        await db.refresh(audit_log)
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
    # Handle empty string case for anonymous users
    if user_id == "":
        result = await db.execute(
            select(AuditLog)
            .filter(AuditLog.user_id.is_(None))
            .order_by(desc(AuditLog.timestamp))
            .offset(offset)
            .limit(limit),
        )
    else:
        result = await db.execute(
            select(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(desc(AuditLog.timestamp))
            .offset(offset)
            .limit(limit),
        )

    return list(result.scalars().all())


async def get_audit_logs_by_event_type(
    db: DBSession,
    event_type: str,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLog]:
    """Get audit logs by event type."""
    result = await db.execute(
        select(AuditLog)
        .filter(AuditLog.event_type == event_type)
        .order_by(desc(AuditLog.timestamp))
        .offset(offset)
        .limit(limit),
    )

    return list(result.scalars().all())


async def get_audit_logs_by_session(
    db: DBSession,
    session_id: str,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLog]:
    """Get audit logs for a specific session."""
    result = await db.execute(
        select(AuditLog)
        .filter(AuditLog.session_id == session_id)
        .order_by(desc(AuditLog.timestamp))
        .offset(offset)
        .limit(limit),
    )

    return list(result.scalars().all())


async def get_recent_audit_logs(
    db: DBSession,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLog]:
    """Get recent audit logs."""
    result = await db.execute(
        select(AuditLog).order_by(desc(AuditLog.timestamp)).offset(offset).limit(limit),
    )

    return list(result.scalars().all())


async def get_failed_audit_logs(
    db: DBSession,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLog]:
    """Get failed audit logs."""
    result = await db.execute(
        select(AuditLog)
        .filter(AuditLog.success.is_(False))
        .order_by(desc(AuditLog.timestamp))
        .offset(offset)
        .limit(limit),
    )

    return list(result.scalars().all())


async def cleanup_old_audit_logs(db: DBSession, days_to_keep: int = 90) -> int:
    """Clean up audit logs older than specified days."""
    cutoff_date = utc_now() - timedelta(days=days_to_keep)

    result = await db.execute(
        select(AuditLog).filter(AuditLog.timestamp < cutoff_date),
    )
    old_logs = result.scalars().all()

    for log in old_logs:
        await db.delete(log)

    await db.commit()
    return len(old_logs)
