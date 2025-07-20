"""
Celery configuration for worker processes.

This file is used by Celery workers to configure the Celery application
and import the necessary task modules.
"""

from app.services.celery import create_celery_app

# Create the Celery app
celery_app = create_celery_app()

# Import tasks to ensure they are registered
if celery_app:
    import app.services.celery_tasks  # noqa: F401
