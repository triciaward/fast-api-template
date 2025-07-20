"""
Unit tests for Celery service module.
"""

from unittest.mock import Mock, patch

from celery import Celery
from celery.result import AsyncResult

from app.services.celery import (
    cancel_task,
    create_celery_app,
    get_celery_app,
    get_celery_stats,
    get_task_status,
    is_celery_enabled,
    submit_task,
)


class TestCeleryService:
    """Test Celery service functions."""

    @patch("app.services.celery.settings")
    def test_create_celery_app(self, mock_settings):
        """Test Celery app creation."""
        # Mock settings
        mock_settings.CELERY_BROKER_URL = "redis://localhost:6379/1"
        mock_settings.CELERY_RESULT_BACKEND = "redis://localhost:6379/1"
        mock_settings.CELERY_TASK_SERIALIZER = "json"
        mock_settings.CELERY_RESULT_SERIALIZER = "json"
        mock_settings.CELERY_ACCEPT_CONTENT = ["json"]
        mock_settings.CELERY_TIMEZONE = "UTC"
        mock_settings.CELERY_ENABLE_UTC = True
        mock_settings.CELERY_TASK_TRACK_STARTED = True
        mock_settings.CELERY_TASK_TIME_LIMIT = 1800
        mock_settings.CELERY_TASK_SOFT_TIME_LIMIT = 1500
        mock_settings.CELERY_WORKER_PREFETCH_MULTIPLIER = 1
        mock_settings.CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

        with patch("app.services.celery.Celery") as mock_celery_class:
            mock_celery_app = Mock(spec=Celery)
            mock_celery_class.return_value = mock_celery_app

            result = create_celery_app()

            # Verify Celery was created with correct parameters
            mock_celery_class.assert_called_once_with(
                "fastapi_template",
                broker="redis://localhost:6379/1",
                backend="redis://localhost:6379/1",
            )

            # Verify configuration was updated
            mock_celery_app.conf.update.assert_called_once()
            # Check that update was called with a dict
            call_args = mock_celery_app.conf.update.call_args
            assert call_args is not None
            config_dict = call_args[0][0] if call_args[0] else call_args[1]
            assert config_dict["task_serializer"] == "json"
            assert config_dict["result_serializer"] == "json"
            assert config_dict["accept_content"] == ["json"]
            assert config_dict["timezone"] == "UTC"
            assert config_dict["enable_utc"] is True
            assert config_dict["task_track_started"] is True
            assert config_dict["task_time_limit"] == 1800
            assert config_dict["task_soft_time_limit"] == 1500
            assert config_dict["worker_prefetch_multiplier"] == 1
            assert config_dict["worker_max_tasks_per_child"] == 1000

            assert result == mock_celery_app

    def test_get_celery_app_singleton(self):
        """Test that get_celery_app returns singleton instance."""
        # Import the module to access the global variable
        import app.services.celery as celery_module

        # Reset the global variable
        celery_module._celery_app = None

        with patch("app.services.celery.create_celery_app") as mock_create:
            mock_app = Mock(spec=Celery)
            mock_create.return_value = mock_app

            # First call should create the app
            result1 = get_celery_app()
            assert result1 == mock_app
            mock_create.assert_called_once()

            # Second call should return the same instance without calling create again
            result2 = get_celery_app()
            assert result2 == mock_app
            # create_celery_app should still only be called once
            mock_create.assert_called_once()

            # Verify the global variable was set
            assert celery_module._celery_app == mock_app

    @patch("app.services.celery.settings")
    def test_is_celery_enabled(self, mock_settings):
        """Test is_celery_enabled function."""
        # Test when enabled
        mock_settings.ENABLE_CELERY = True
        assert is_celery_enabled() is True

        # Test when disabled
        mock_settings.ENABLE_CELERY = False
        assert is_celery_enabled() is False

    @patch("app.services.celery.is_celery_enabled")
    @patch("app.services.celery.get_celery_app")
    def test_submit_task_success(self, mock_get_app, mock_enabled):
        """Test successful task submission."""
        mock_enabled.return_value = True
        mock_app = Mock(spec=Celery)
        mock_get_app.return_value = mock_app

        mock_result = Mock(spec=AsyncResult)
        mock_result.id = "test-task-id"
        mock_app.send_task.return_value = mock_result

        result = submit_task("test_task", "arg1", kwarg1="value1")

        assert result == mock_result
        mock_app.send_task.assert_called_once_with(
            "test_task", args=("arg1",), kwargs={"kwarg1": "value1"}
        )

    @patch("app.services.celery.is_celery_enabled")
    def test_submit_task_disabled(self, mock_enabled):
        """Test task submission when Celery is disabled."""
        mock_enabled.return_value = False

        result = submit_task("test_task", "arg1")

        assert result is None
        # The actual logging happens, but we don't need to mock it for this test

    @patch("app.services.celery.is_celery_enabled")
    @patch("app.services.celery.get_celery_app")
    def test_submit_task_exception(self, mock_get_app, mock_enabled):
        """Test task submission with exception."""
        mock_enabled.return_value = True
        mock_app = Mock(spec=Celery)
        mock_get_app.return_value = mock_app
        mock_app.send_task.side_effect = Exception("Test error")

        result = submit_task("test_task", "arg1")

        assert result is None
        # The actual logging happens, but we don't need to mock it for this test

    @patch("app.services.celery.is_celery_enabled")
    @patch("app.services.celery.get_celery_app")
    @patch("app.services.celery.AsyncResult")
    def test_get_task_status_success(self, mock_async_result, mock_get_app, mock_enabled):
        """Test successful task status retrieval."""
        mock_enabled.return_value = True
        mock_app = Mock(spec=Celery)
        mock_get_app.return_value = mock_app

        mock_result = Mock(spec=AsyncResult)
        mock_result.status = "SUCCESS"
        mock_result.ready.return_value = True
        mock_result.successful.return_value = True
        mock_result.failed.return_value = False
        mock_result.result = {"status": "completed"}
        mock_async_result.return_value = mock_result

        result = get_task_status("test-task-id")

        assert result["task_id"] == "test-task-id"
        assert result["status"] == "SUCCESS"
        assert result["ready"] is True
        assert result["successful"] is True
        assert result["failed"] is False
        assert result["result"] == {"status": "completed"}

    @patch("app.services.celery.is_celery_enabled")
    def test_get_task_status_disabled(self, mock_enabled):
        """Test task status retrieval when Celery is disabled."""
        mock_enabled.return_value = False

        result = get_task_status("test-task-id")

        assert result is None

    @patch("app.services.celery.is_celery_enabled")
    @patch("app.services.celery.get_celery_app")
    def test_cancel_task_success(self, mock_get_app, mock_enabled):
        """Test successful task cancellation."""
        mock_enabled.return_value = True
        mock_app = Mock(spec=Celery)
        mock_get_app.return_value = mock_app

        result = cancel_task("test-task-id")

        assert result is True
        mock_app.control.revoke.assert_called_once_with(
            "test-task-id", terminate=True)
        # The actual logging happens, but we don't need to mock it for this test

    @patch("app.services.celery.is_celery_enabled")
    def test_cancel_task_disabled(self, mock_enabled):
        """Test task cancellation when Celery is disabled."""
        mock_enabled.return_value = False

        result = cancel_task("test-task-id")

        assert result is False

    @patch("app.services.celery.is_celery_enabled")
    @patch("app.services.celery.get_celery_app")
    @patch("app.services.celery.get_active_tasks")
    @patch("app.services.celery.settings")
    def test_get_celery_stats_success(
        self, mock_settings, mock_get_active, mock_get_app, mock_enabled
    ):
        """Test successful Celery stats retrieval."""
        mock_enabled.return_value = True
        mock_app = Mock(spec=Celery)
        mock_get_app.return_value = mock_app

        mock_settings.CELERY_BROKER_URL = "redis://localhost:6379/1"
        mock_settings.CELERY_RESULT_BACKEND = "redis://localhost:6379/1"

        mock_inspect = Mock()
        mock_app.control.inspect.return_value = mock_inspect
        mock_inspect.active.return_value = {"worker1": []}
        mock_inspect.registered.return_value = {"worker1": ["task1", "task2"]}

        mock_get_active.return_value = [{"task_id": "task1"}]

        result = get_celery_stats()

        assert result["enabled"] is True
        assert result["broker_url"] == "redis://localhost:6379/1"
        assert result["result_backend"] == "redis://localhost:6379/1"
        assert result["active_workers"] == 1
        assert result["registered_tasks"] == 1
        assert result["active_tasks"] == 1

    @patch("app.services.celery.is_celery_enabled")
    def test_get_celery_stats_disabled(self, mock_enabled):
        """Test Celery stats retrieval when Celery is disabled."""
        mock_enabled.return_value = False

        result = get_celery_stats()

        assert result["enabled"] is False
