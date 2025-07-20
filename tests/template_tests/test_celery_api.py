"""
Unit tests for Celery API endpoints.
"""

import os
from unittest.mock import Mock, PropertyMock, patch

from fastapi.testclient import TestClient

# Set environment variables for Celery tests
os.environ["ENABLE_CELERY"] = "true"
os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"
os.environ["CELERY_TASK_EAGER_PROPAGATES"] = "true"

# Import app after environment variables are set


class TestCeleryAPI:
    """Test Celery API endpoints."""

    def test_celery_routes_exist(self):
        """Test that Celery routes are included in the app."""
        # Create a new app instance with Celery enabled
        import os
        import sys

        # Set environment variables
        os.environ["ENABLE_CELERY"] = "true"
        os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"
        os.environ["CELERY_TASK_EAGER_PROPAGATES"] = "true"

        # Force reload of config
        sys.modules.pop("app.core.config", None)

        # Import app after environment is set
        from app.main import app

        # Create test client with the new app
        with TestClient(app) as client:
            # Check if the route exists
            response = client.get("/api/v1/celery/status")
            # Should not be 404 - either 200 (if Celery is enabled) or 503 (if disabled)
            assert response.status_code in [200, 503]

    @patch("app.services.celery.is_celery_enabled")
    def test_submit_celery_task_enabled(self, mock_enabled, client: TestClient):
        """Test submitting a Celery task when enabled."""
        mock_enabled.return_value = True

        with patch("app.api.api_v1.endpoints.celery.submit_task") as mock_submit:
            # Create a proper mock that returns a string for the id attribute
            mock_result = Mock()
            mock_result.id = "test-task-id"
            # Ensure the id is a string, not a Mock object
            type(mock_result).id = PropertyMock(return_value="test-task-id")
            mock_submit.return_value = mock_result

            task_data = {
                "task_name": "app.services.celery_tasks.send_email_task",
                "args": ["test@example.com", "Test Subject", "Test Body"],
                "kwargs": {"priority": "high"},
            }

            response = client.post("/api/v1/celery/tasks/submit", json=task_data)

            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "test-task-id"
            assert data["task_name"] == "app.services.celery_tasks.send_email_task"
            assert data["status"] == "PENDING"
            assert data["message"] == "Task submitted successfully"

            mock_submit.assert_called_once_with(
                "app.services.celery_tasks.send_email_task",
                "test@example.com",
                "Test Subject",
                "Test Body",
                priority="high",
            )

    @patch("app.services.celery.is_celery_enabled")
    def test_submit_celery_task_failure(self, mock_enabled, client: TestClient):
        """Test submitting a Celery task with failure."""
        mock_enabled.return_value = True

        with patch("app.api.api_v1.endpoints.celery.submit_task") as mock_submit:
            mock_submit.return_value = None

            task_data = {
                "task_name": "app.services.celery_tasks.send_email_task",
                "args": ["test@example.com", "Test Subject", "Test Body"],
                "kwargs": {},
            }

            response = client.post("/api/v1/celery/tasks/submit", json=task_data)

            assert response.status_code == 500
            assert "Failed to submit task" in response.json()["detail"]

    @patch("app.services.celery.is_celery_enabled")
    def test_get_task_status_not_found(self, mock_enabled, client: TestClient):
        """Test getting task status for non-existent task."""
        mock_enabled.return_value = True

        with patch("app.api.api_v1.endpoints.celery.get_task_status") as mock_status:
            mock_status.return_value = None

            response = client.get("/api/v1/celery/tasks/non-existent-id/status")

            assert response.status_code == 404
            assert "Task not found" in response.json()["detail"]

    @patch("app.services.celery.is_celery_enabled")
    def test_submit_email_task_enabled(self, mock_enabled, client: TestClient):
        """Test submitting email task when enabled."""
        mock_enabled.return_value = True

        with patch("app.api.api_v1.endpoints.celery.submit_task") as mock_submit:
            # Create a proper mock that returns a string for the id attribute
            mock_result = Mock()
            type(mock_result).id = PropertyMock(return_value="email-task-id")
            mock_submit.return_value = mock_result

            response = client.post(
                "/api/v1/celery/tasks/send-email",
                params={
                    "to_email": "test@example.com",
                    "subject": "Test Subject",
                    "body": "Test Body",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "email-task-id"
            assert data["task_name"] == "send_email_task"
            assert data["status"] == "PENDING"
            assert data["message"] == "Email task submitted successfully"

            mock_submit.assert_called_once_with(
                "app.services.celery_tasks.send_email_task",
                "test@example.com",
                "Test Subject",
                "Test Body",
            )

    @patch("app.services.celery.is_celery_enabled")
    def test_submit_data_processing_task_enabled(
        self, mock_enabled, client: TestClient
    ):
        """Test submitting data processing task when enabled."""
        mock_enabled.return_value = True

        with patch("app.api.api_v1.endpoints.celery.submit_task") as mock_submit:
            # Create a proper mock that returns a string for the id attribute
            mock_result = Mock()
            type(mock_result).id = PropertyMock(return_value="data-task-id")
            mock_submit.return_value = mock_result

            data = [{"id": 1, "name": "item1"}, {"id": 2, "name": "item2"}]

            response = client.post("/api/v1/celery/tasks/process-data", json=data)

            assert response.status_code == 200
            data_response = response.json()
            assert data_response["task_id"] == "data-task-id"
            assert data_response["task_name"] == "process_data_task"
            assert data_response["status"] == "PENDING"
            assert "2 items" in data_response["message"]

            mock_submit.assert_called_once_with(
                "app.services.celery_tasks.process_data_task",
                [{"id": 1, "name": "item1"}, {"id": 2, "name": "item2"}],
            )

    @patch("app.services.celery.is_celery_enabled")
    def test_submit_cleanup_task_enabled(self, mock_enabled, client: TestClient):
        """Test submitting cleanup task when enabled."""
        mock_enabled.return_value = True

        with patch("app.api.api_v1.endpoints.celery.submit_task") as mock_submit:
            # Create a proper mock that returns a string for the id attribute
            mock_result = Mock()
            type(mock_result).id = PropertyMock(return_value="cleanup-task-id")
            mock_submit.return_value = mock_result

            response = client.post("/api/v1/celery/tasks/cleanup")

            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "cleanup-task-id"
            assert data["task_name"] == "cleanup_task"
            assert data["status"] == "PENDING"
            assert data["message"] == "Cleanup task submitted successfully"

            mock_submit.assert_called_once_with(
                "app.services.celery_tasks.cleanup_task"
            )

    @patch("app.services.celery.is_celery_enabled")
    def test_submit_long_running_task_enabled(self, mock_enabled, client: TestClient):
        """Test submitting long running task when enabled."""
        mock_enabled.return_value = True

        with patch("app.api.api_v1.endpoints.celery.submit_task") as mock_submit:
            # Create a proper mock that returns a string for the id attribute
            mock_result = Mock()
            type(mock_result).id = PropertyMock(return_value="long-task-id")
            mock_submit.return_value = mock_result

            response = client.post(
                "/api/v1/celery/tasks/long-running", params={"duration": 120}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "long-task-id"
            assert data["task_name"] == "long_running_task"
            assert data["status"] == "PENDING"
            assert "120s" in data["message"]

            mock_submit.assert_called_once_with(
                "app.services.celery_tasks.long_running_task", 120
            )

    @patch("app.services.celery.is_celery_enabled")
    def test_submit_long_running_task_default_duration(
        self, mock_enabled, client: TestClient
    ):
        """Test submitting long running task with default duration."""
        mock_enabled.return_value = True

        with patch("app.api.api_v1.endpoints.celery.submit_task") as mock_submit:
            # Create a proper mock that returns a string for the id attribute
            mock_result = Mock()
            type(mock_result).id = PropertyMock(return_value="long-task-id")
            mock_submit.return_value = mock_result

            response = client.post("/api/v1/celery/tasks/long-running")

            assert response.status_code == 200
            data = response.json()
            assert "60s" in data["message"]

            mock_submit.assert_called_once_with(
                "app.services.celery_tasks.long_running_task", 60
            )
