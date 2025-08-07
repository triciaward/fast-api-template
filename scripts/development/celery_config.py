"""
Celery configuration for worker processes.

This file is used by Celery workers to configure the Celery application
and import the necessary task modules.
"""

from app.services.background.celery_app import celery_app

# Use the existing Celery app instance

# Import tasks to ensure they are registered
if celery_app:
    import app.services.background.celery_tasks  # noqa: F401
