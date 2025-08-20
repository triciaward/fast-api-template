"""
Celery service for background task processing.

This module provides Celery integration for handling background tasks
like email sending, data processing, and cleanup jobs.

This file should NOT define or register any Celery tasks. Tasks are defined in celery_tasks.py and only imported when Celery is enabled.
"""

from typing import Any, TypedDict

from celery.result import AsyncResult
from celery.utils.log import get_task_logger

from app.core.config.config import settings
from app.core.config.logging_config import get_app_logger
from app.services.background.celery_app import celery_app

app_logger = get_app_logger()
celery_logger = get_task_logger(__name__)


class TaskStatusTD(TypedDict, total=False):
    task_id: str
    status: str
    ready: bool
    successful: bool
    failed: bool
    result: Any
    error: str


class ActiveTaskTD(TypedDict):
    task_id: str
    name: str
    worker: str
    args: list[Any]
    kwargs: dict[str, Any]
    time_start: float | None


class CeleryStatsTD(TypedDict, total=False):
    enabled: bool
    broker_url: str | None
    result_backend: str | None
    active_workers: int | None
    registered_tasks: int | None
    active_tasks: int | None
    error: str | None


def get_celery_app() -> Any:
    """Get the global Celery app instance."""
    return celery_app


def is_celery_enabled() -> bool:
    return settings.ENABLE_CELERY


def submit_task(task_name: str, *args: Any, **kwargs: Any) -> AsyncResult | None:
    if not is_celery_enabled():
        app_logger.warning(
            "Attempted to submit task but Celery is disabled",
            task_name=task_name,
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
            "Failed to submit task",
            task_name=task_name,
            error=str(e),
            exc_info=True,
        )
        return None
    else:
        return result


def get_task_status(task_id: str) -> TaskStatusTD | None:
    if not is_celery_enabled():
        return None

    try:
        app = get_celery_app()
        result = AsyncResult(task_id, app=app)
        status_info: TaskStatusTD = {
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
            "Failed to get task status",
            task_id=task_id,
            error=str(e),
            exc_info=True,
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
            "Failed to cancel task",
            task_id=task_id,
            error=str(e),
            exc_info=True,
        )
        return False
    else:
        return True


def get_active_tasks() -> list[ActiveTaskTD]:
    if not is_celery_enabled():
        return []

    try:
        app = get_celery_app()
        active_tasks = app.control.inspect().active()
        if not active_tasks:
            return []
        return [
            ActiveTaskTD(
                task_id=str(task.get("id", "")),
                name=str(task.get("name", "")),
                worker=str(worker),
                args=list(task.get("args", [])),
                kwargs=dict(task.get("kwargs", {})),
                time_start=task.get("time_start"),
            )
            for worker, worker_tasks in active_tasks.items()
            for task in worker_tasks
        ]
    except Exception as e:
        app_logger.error("Failed to get active tasks", error=str(e), exc_info=True)
        return []


def get_celery_stats() -> CeleryStatsTD:
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
