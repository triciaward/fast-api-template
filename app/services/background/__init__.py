"""Background task processing services."""

from .celery import (
    cancel_task,
    get_active_tasks,
    get_celery_app,
    get_celery_stats,
    get_task_status,
    is_celery_enabled,
    submit_task,
)
from .celery_app import celery_app

# Import tasks only if available
try:
    from .celery_tasks import (
        cleanup_task,
        long_running_task,
        periodic_health_check,
        permanently_delete_accounts_task,
        process_data_task,
        send_email_task,
    )
except ImportError:
    # Fallback if Celery dependencies not available
    send_email_task = None
    process_data_task = None
    cleanup_task = None
    long_running_task = None
    periodic_health_check = None
    permanently_delete_accounts_task = None

__all__ = [
    "celery_app",
    "get_celery_app",
    "is_celery_enabled",
    "submit_task",
    "get_task_status",
    "cancel_task",
    "get_active_tasks",
    "get_celery_stats",
    "send_email_task",
    "process_data_task",
    "cleanup_task",
    "long_running_task",
    "periodic_health_check",
    "permanently_delete_accounts_task",
]
