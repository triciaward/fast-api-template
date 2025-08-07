"""
Tests for Celery services.

This module tests the Celery app configuration and task definitions.
"""

from unittest.mock import MagicMock, patch

from app.services.celery_app import celery_app
from app.services.celery_tasks import (
    cleanup_task,
    long_running_task,
    periodic_health_check,
    permanently_delete_accounts_task,
    process_data_task,
    send_email_task,
)


class TestCeleryAppConfiguration:
    """Test Celery app configuration."""

    def test_celery_app_creation(self):
        """Test that Celery app is created with correct name."""
        assert celery_app.main == "fastapi_template"

    def test_celery_app_configuration(self):
        """Test that Celery app has correct configuration."""
        # Test that key configuration options are set
        assert celery_app.conf.task_serializer is not None
        assert celery_app.conf.result_serializer is not None
        assert celery_app.conf.accept_content is not None
        assert celery_app.conf.timezone is not None
        assert celery_app.conf.enable_utc is not None
        assert celery_app.conf.task_track_started is not None
        assert celery_app.conf.task_time_limit is not None
        assert celery_app.conf.task_soft_time_limit is not None
        assert celery_app.conf.worker_prefetch_multiplier is not None
        assert celery_app.conf.worker_max_tasks_per_child is not None
        assert celery_app.conf.task_always_eager is not None
        assert celery_app.conf.task_eager_propagates is not None
        assert celery_app.conf.result_expires == 3600
        assert celery_app.conf.worker_disable_rate_limits is False
        assert celery_app.conf.worker_send_task_events is True
        assert celery_app.conf.task_send_sent_event is True

    def test_celery_app_broker_url(self):
        """Test that Celery app has broker URL configured."""
        # This will use the test configuration
        assert celery_app.conf.broker_url is not None

    def test_celery_app_result_backend(self):
        """Test that Celery app has result backend configured."""
        # This will use the test configuration
        assert celery_app.conf.result_backend is not None


class TestCeleryTasks:
    """Test Celery task definitions."""

    def test_send_email_task(self):
        """Test send_email_task function."""
        result = send_email_task("test@example.com", "Test Subject", "Test Body")
        assert result["status"] == "sent"
        assert result["to"] == "test@example.com"
        assert result["subject"] == "Test Subject"

    def test_process_data_task(self):
        """Test process_data_task function."""
        test_data = [{"id": 1}, {"id": 2}, {"id": 3}]
        result = process_data_task(test_data)
        assert result["status"] == "processed"
        assert result["count"] == 3

    def test_cleanup_task(self):
        """Test cleanup_task function."""
        result = cleanup_task()
        assert result["status"] == "cleanup complete"

    def test_long_running_task(self):
        """Test long_running_task function."""
        result = long_running_task(duration=1)  # Short duration for testing
        assert result["status"] == "done"
        assert result["duration"] == 1

    def test_periodic_health_check(self):
        """Test periodic_health_check function."""
        result = periodic_health_check()
        assert result["status"] == "healthy"

    @patch("app.database.database.get_db_sync")
    @patch("app.crud.user.permanently_delete_user_sync")
    @patch("app.core.logging_config.get_app_logger")
    def test_permanently_delete_accounts_task_success(
        self,
        mock_logger,
        mock_delete_user,
        mock_get_db,
    ):
        """Test permanently_delete_accounts_task with successful deletion."""
        # Mock database and user
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = "test-user-id"
        mock_user.email = "test@example.com"
        mock_user.username = "testuser"
        mock_user.is_deleted = False
        mock_user.deletion_scheduled_for = "2023-01-01T00:00:00"
        mock_user.deletion_confirmed_at = "2023-01-01T00:00:00"

        # Mock database query result
        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_user]
        mock_get_db.return_value = iter([mock_db])
        mock_delete_user.return_value = True

        # Mock logger
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance

        # Run the task
        result = permanently_delete_accounts_task()

        # Verify the result
        assert result["status"] == "completed"
        assert result["accounts_deleted"] == 1
        assert result["reminders_sent"] == 0

        # Verify logger was called
        mock_logger_instance.info.assert_called()

    @patch("app.database.database.get_db_sync")
    @patch("app.crud.user.permanently_delete_user_sync")
    @patch("app.core.logging_config.get_app_logger")
    def test_permanently_delete_accounts_task_no_accounts(
        self,
        mock_logger,
        _mock_delete_user,
        mock_get_db,
    ):
        """Test permanently_delete_accounts_task with no accounts to delete."""
        # Mock database with no users
        mock_db = MagicMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        mock_get_db.return_value = iter([mock_db])

        # Mock logger
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance

        # Run the task
        result = permanently_delete_accounts_task()

        # Verify the result
        assert result["status"] == "completed"
        assert result["accounts_deleted"] == 0
        assert result["reminders_sent"] == 0

    @patch("app.database.database.get_db_sync")
    @patch("app.core.logging_config.get_app_logger")
    def test_permanently_delete_accounts_task_exception(self, mock_logger, mock_get_db):
        """Test permanently_delete_accounts_task with database exception."""
        # Mock database to raise exception
        mock_get_db.side_effect = Exception("Database error")

        # Mock logger
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance

        # Run the task
        result = permanently_delete_accounts_task()

        # Verify the result
        assert result["status"] == "failed"
        assert "error" in result

        # Verify logger was called
        mock_logger_instance.error.assert_called()


class TestCeleryTaskRegistration:
    """Test that Celery tasks are properly registered."""

    def test_tasks_registered_with_celery_app(self):
        """Test that tasks are registered with the Celery app."""
        # Check that tasks are registered
        assert "app.services.celery_tasks.send_email_task" in celery_app.tasks
        assert "app.services.celery_tasks.process_data_task" in celery_app.tasks
        assert "app.services.celery_tasks.cleanup_task" in celery_app.tasks
        assert "app.services.celery_tasks.long_running_task" in celery_app.tasks
        assert "app.services.celery_tasks.periodic_health_check" in celery_app.tasks
        assert (
            "app.services.celery_tasks.permanently_delete_accounts_task"
            in celery_app.tasks
        )

    def test_task_names_match_registration(self):
        """Test that task names match their registration names."""
        assert send_email_task.name == "app.services.celery_tasks.send_email_task"
        assert process_data_task.name == "app.services.celery_tasks.process_data_task"
        assert cleanup_task.name == "app.services.celery_tasks.cleanup_task"
        assert long_running_task.name == "app.services.celery_tasks.long_running_task"
        assert (
            periodic_health_check.name
            == "app.services.celery_tasks.periodic_health_check"
        )
        assert (
            permanently_delete_accounts_task.name
            == "app.services.celery_tasks.permanently_delete_accounts_task"
        )
