"""
Celery task definitions for background processing.

This module is only imported when Celery is enabled, and is not loaded by the main app unless USE_CELERY/ENABLE_CELERY is true.
"""

import time
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
