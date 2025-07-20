from typing import Any, Optional, Union

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.logging_config import get_auth_logger
from app.crud.audit_log import create_audit_log, create_audit_log_sync
from app.models.models import User

# Type alias for both sync and async sessions
DBSession = Union[AsyncSession, Session]

# Get the auth logger for structlog integration
auth_logger = get_auth_logger()


def get_client_ip(request: Request) -> Optional[str]:
    """Extract client IP address from request, handling proxies."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host if request.client else None


def get_user_agent(request: Request) -> Optional[str]:
    """Extract user agent from request."""
    return request.headers.get("User-Agent")


async def log_event(
    db: DBSession,
    event_type: str,
    request: Request,
    user: Optional[User] = None,
    success: bool = True,
    context: Optional[dict[str, Any]] = None,
    session_id: Optional[str] = None,
) -> None:
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    user_id = str(user.id) if user else None
    audit_log = await create_audit_log(
        db=db,
        event_type=event_type,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
        context=context,
        session_id=session_id,
    )
    log_context = {
        "event_type": event_type,
        "user_id": user_id,
        "ip_address": ip_address,
        "success": success,
        "audit_log_id": str(audit_log.id),
    }
    if context:
        log_context.update(context)
    if session_id:
        log_context["session_id"] = session_id
    auth_logger.info(
        "Audit log event",
        **log_context
    )


def log_event_sync(
    db: Session,
    event_type: str,
    request: Request,
    user: Optional[User] = None,
    success: bool = True,
    context: Optional[dict[str, Any]] = None,
    session_id: Optional[str] = None,
) -> None:
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    user_id = str(user.id) if user else None
    audit_log = create_audit_log_sync(
        db=db,
        event_type=event_type,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
        context=context,
        session_id=session_id,
    )
    log_context = {
        "event_type": event_type,
        "user_id": user_id,
        "ip_address": ip_address,
        "success": success,
        "audit_log_id": str(audit_log.id),
    }
    if context:
        log_context.update(context)
    if session_id:
        log_context["session_id"] = session_id
    auth_logger.info(
        "Audit log event",
        **log_context
    )


# Convenience functions for common audit events
async def log_login_attempt(
    db: DBSession,
    request: Request,
    user: Optional[User] = None,
    success: bool = True,
    oauth_provider: Optional[str] = None,
) -> None:
    context = {}
    if oauth_provider:
        context["oauth_provider"] = oauth_provider
    event_type = "login_success" if success else "login_failed"
    await log_event(
        db=db,
        event_type=event_type,
        request=request,
        user=user,
        success=success,
        context=context,
    )


async def log_logout(
    db: DBSession,
    request: Request,
    user: User,
) -> None:
    await log_event(
        db=db,
        event_type="logout",
        request=request,
        user=user,
        success=True,
    )


async def log_password_change(
    db: DBSession,
    request: Request,
    user: User,
    change_type: str = "password_change",
) -> None:
    await log_event(
        db=db,
        event_type=change_type,
        request=request,
        user=user,
        success=True,
        context={"change_type": change_type},
    )


async def log_account_deletion(
    db: DBSession,
    request: Request,
    user: User,
    deletion_stage: str = "deletion_requested",
) -> None:
    await log_event(
        db=db,
        event_type="account_deletion",
        request=request,
        user=user,
        success=True,
        context={"deletion_stage": deletion_stage},
    )


async def log_email_verification(
    db: DBSession,
    request: Request,
    user: User,
    success: bool = True,
) -> None:
    await log_event(
        db=db,
        event_type="email_verification",
        request=request,
        user=user,
        success=success,
    )


async def log_oauth_login(
    db: DBSession,
    request: Request,
    user: User,
    oauth_provider: str,
    success: bool = True,
) -> None:
    await log_event(
        db=db,
        event_type="oauth_login",
        request=request,
        user=user,
        success=success,
        context={"oauth_provider": oauth_provider},
    )


def log_login_attempt_sync(
    db: Session,
    request: Request,
    user: Optional[User] = None,
    success: bool = True,
    oauth_provider: Optional[str] = None,
) -> None:
    context = {}
    if oauth_provider:
        context["oauth_provider"] = oauth_provider
    event_type = "login_success" if success else "login_failed"
    log_event_sync(
        db=db,
        event_type=event_type,
        request=request,
        user=user,
        success=success,
        context=context,
    )


def log_password_change_sync(
    db: Session,
    request: Request,
    user: User,
    change_type: str = "password_change",
) -> None:
    log_event_sync(
        db=db,
        event_type=change_type,
        request=request,
        user=user,
        success=True,
        context={"change_type": change_type},
    )
