"""
Celery service for background task processing.

This module provides Celery integration for handling background tasks
like email sending, data processing, and cleanup jobs.

This file should NOT define or register any Celery tasks. Tasks are defined in celery_tasks.py and only imported when Celery is enabled.
"""

from typing import Any

from celery import Celery
from celery.result import AsyncResult
from celery.utils.log import get_task_logger

from app.core.config import settings
from app.core.logging_config import get_app_logger

app_logger = get_app_logger()
celery_logger = get_task_logger(__name__)

_celery_app: Celery | None = None


def create_celery_app() -> Celery:
    app = Celery(
        "fastapi_template",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )
    app.conf.update(
        task_serializer=settings.CELERY_TASK_SERIALIZER,
        result_serializer=settings.CELERY_RESULT_SERIALIZER,
        accept_content=settings.CELERY_ACCEPT_CONTENT,
        timezone=settings.CELERY_TIMEZONE,
        enable_utc=settings.CELERY_ENABLE_UTC,
        task_track_started=settings.CELERY_TASK_TRACK_STARTED,
        task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
        task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
        worker_prefetch_multiplier=settings.CELERY_WORKER_PREFETCH_MULTIPLIER,
        worker_max_tasks_per_child=settings.CELERY_WORKER_MAX_TASKS_PER_CHILD,
        task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
        task_eager_propagates=settings.CELERY_TASK_EAGER_PROPAGATES,
        result_expires=3600,
        worker_disable_rate_limits=False,
        worker_send_task_events=True,
        task_send_sent_event=True,
    )
    return app


def get_celery_app() -> Celery:
    global _celery_app
    if _celery_app is None:
        _celery_app = create_celery_app()
    return _celery_app


def is_celery_enabled() -> bool:
    return settings.ENABLE_CELERY


def submit_task(task_name: str, *args: Any, **kwargs: Any) -> AsyncResult | None:
    if not is_celery_enabled():
        app_logger.warning(
            "Attempted to submit task but Celery is disabled", task_name=task_name,
        )
        return None
    try:
        app = get_celery_app()
        result = app.send_task(task_name, args=args, kwargs=kwargs)
        app_logger.info(
            "Task submitted successfully",
            task_name=task_name,
            task_id=result.id,
            args=args,
            kwargs=kwargs,
        )
    except Exception as e:
        app_logger.error(
            "Failed to submit task", task_name=task_name, error=str(e), exc_info=True,
        )
        return None
    else:
        return result


def get_task_status(task_id: str) -> dict[str, Any] | None:
    if not is_celery_enabled():
        return None

    try:
        app = get_celery_app()
        result = AsyncResult(task_id, app=app)
        status_info = {
            "task_id": task_id,
            "status": result.status,
            "ready": result.ready(),
            "successful": result.successful(),
            "failed": result.failed(),
        }
        if result.ready():
            if result.successful():
                status_info["result"] = result.result
            else:
                status_info["error"] = str(result.info)
    except Exception as e:
        app_logger.error(
            "Failed to get task status", task_id=task_id, error=str(e), exc_info=True,
        )
        return None
    else:
        return status_info


def cancel_task(task_id: str) -> bool:
    if not is_celery_enabled():
        return False

    try:
        app = get_celery_app()
        app.control.revoke(task_id, terminate=True)
        app_logger.info("Task cancelled successfully", task_id=task_id)
    except Exception as e:
        app_logger.error(
            "Failed to cancel task", task_id=task_id, error=str(e), exc_info=True,
        )
        return False
    else:
        return True


def get_active_tasks() -> list[dict[str, Any]]:
    if not is_celery_enabled():
        return []

    try:
        app = get_celery_app()
        active_tasks = app.control.inspect().active()
        if not active_tasks:
            return []
        return [
            {
                "task_id": task["id"],
                "name": task["name"],
                "worker": worker,
                "args": task.get("args", []),
                "kwargs": task.get("kwargs", {}),
                "time_start": task.get("time_start"),
            }
            for worker, worker_tasks in active_tasks.items()
            for task in worker_tasks
        ]
    except Exception as e:
        app_logger.error("Failed to get active tasks", error=str(e), exc_info=True)
        return []


def get_celery_stats() -> dict[str, Any]:
    if not is_celery_enabled():
        return {"enabled": False}

    try:
        app = get_celery_app()
        inspect = app.control.inspect()
        return {
            "enabled": True,
            "broker_url": settings.CELERY_BROKER_URL,
            "result_backend": settings.CELERY_RESULT_BACKEND,
            "active_workers": len(inspect.active() or {}),
            "registered_tasks": len(inspect.registered() or {}),
            "active_tasks": len(get_active_tasks()),
        }
    except Exception as e:
        app_logger.error("Failed to get Celery stats", error=str(e), exc_info=True)
        return {"enabled": False, "error": str(e)}
