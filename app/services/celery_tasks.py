"""
Celery task definitions for background processing.

This module is only imported when Celery is enabled, and is not loaded by the main app unless USE_CELERY/ENABLE_CELERY is true.
"""

import time
from datetime import UTC
from typing import Any

from app.services.celery_app import celery_app


@celery_app.task(name="app.services.celery_tasks.send_email_task")
def send_email_task(to_email: str, subject: str, body: str) -> dict[str, Any]:
    # Example: Replace with real email logic
    time.sleep(1)
    return {"status": "sent", "to": to_email, "subject": subject}


@celery_app.task(name="app.services.celery_tasks.process_data_task")
def process_data_task(data: list[dict[str, Any]]) -> dict[str, Any]:
    time.sleep(1)
    return {"status": "processed", "count": len(data)}


@celery_app.task(name="app.services.celery_tasks.cleanup_task")
def cleanup_task() -> dict[str, Any]:
    time.sleep(1)
    return {"status": "cleanup complete"}


@celery_app.task(name="app.services.celery_tasks.long_running_task")
def long_running_task(duration: int = 60) -> dict[str, Any]:
    for _ in range(duration):
        time.sleep(1)
    return {"status": "done", "duration": duration}


@celery_app.task(name="app.services.celery_tasks.periodic_health_check")
def periodic_health_check() -> dict[str, Any]:
    time.sleep(1)
    return {"status": "healthy"}


@celery_app.task(name="app.services.celery_tasks.permanently_delete_accounts_task")
def permanently_delete_accounts_task() -> dict[str, Any]:
    """Permanently delete accounts that have passed their grace period."""
    from datetime import datetime

    from sqlalchemy import select

    from app.core.config import settings
    from app.core.logging_config import get_app_logger
    from app.crud import user as crud_user
    from app.database.database import get_db_sync
    from app.models import User
    from app.services import email_service

    logger = get_app_logger()
    logger.info("Starting permanent account deletion task")

    def utc_now() -> datetime:
        """Get current UTC datetime (replaces deprecated datetime.utcnow())."""
        return datetime.now(UTC)

    try:
        db = next(get_db_sync())
        deleted_count = 0
        reminder_sent_count = 0

        # Find accounts scheduled for deletion that have passed their grace period
        accounts_to_delete = (
            db.execute(
                select(User).filter(
                    User.deletion_scheduled_for <= utc_now(),
                    User.is_deleted == False,  # noqa: E712
                    User.deletion_confirmed_at.isnot(None),
                )
            )
            .scalars()
            .all()
        )

        for user in accounts_to_delete:
            try:
                # Mark as permanently deleted
                success = crud_user.permanently_delete_user_sync(db, str(user.id))
                if success:
                    deleted_count += 1
                    logger.info(
                        "Account permanently deleted",
                        user_id=str(user.id),
                        email=user.email,
                        username=user.username,
                    )
                else:
                    logger.error(
                        "Failed to permanently delete account",
                        user_id=str(user.id),
                        email=user.email,
                    )
            except Exception as e:
                logger.error(
                    "Error deleting account",
                    user_id=str(user.id),
                    email=user.email,
                    error=str(e),
                    exc_info=True,
                )

        # Send reminder emails for accounts approaching deletion
        from datetime import timedelta

        for reminder_days in settings.ACCOUNT_DELETION_REMINDER_DAYS:
            reminder_date = utc_now() + timedelta(days=reminder_days)

            accounts_for_reminder = (
                db.execute(
                    select(User).filter(
                        User.deletion_scheduled_for <= reminder_date,
                        User.deletion_scheduled_for > utc_now(),
                        User.is_deleted == False,  # noqa: E712
                        User.deletion_confirmed_at.isnot(None),
                    )
                )
                .scalars()
                .all()
            )

            for user in accounts_for_reminder:
                try:
                    # Calculate days remaining
                    days_remaining = (user.deletion_scheduled_for - utc_now()).days

                    # Send reminder email
                    if email_service and email_service.is_configured():
                        email_sent = email_service.send_account_deletion_reminder_email(
                            str(user.email),
                            str(user.username),
                            days_remaining,
                            user.deletion_scheduled_for.strftime(
                                "%Y-%m-%d %H:%M:%S UTC"
                            ),
                        )

                        if email_sent:
                            reminder_sent_count += 1
                            logger.info(
                                "Account deletion reminder sent",
                                user_id=str(user.id),
                                email=user.email,
                                days_remaining=days_remaining,
                            )
                        else:
                            logger.error(
                                "Failed to send account deletion reminder",
                                user_id=str(user.id),
                                email=user.email,
                            )
                except Exception as e:
                    logger.error(
                        "Error sending account deletion reminder",
                        user_id=str(user.id),
                        email=user.email,
                        error=str(e),
                        exc_info=True,
                    )

        logger.info(
            "Permanent account deletion task completed",
            accounts_deleted=deleted_count,
            reminders_sent=reminder_sent_count,
        )

        return {
            "status": "completed",
            "accounts_deleted": deleted_count,
            "reminders_sent": reminder_sent_count,
        }

    except Exception as e:
        logger.error(
            "Permanent account deletion task failed",
            error=str(e),
            exc_info=True,
        )
        return {"status": "failed", "error": str(e)}
