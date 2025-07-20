"""
These tests cover Celery status, health, and inspect APIs using mocks.
They're non-critical and depend on accurate mocking of Redis/Celery internals.
These tests are separated from the main test suite due to complex mocking requirements.
"""

# Set environment variable before importing app
import os
from unittest.mock import Mock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app

os.environ["ENABLE_CELERY"] = "true"


class TestCeleryMockedAPIs:
    """Test Celery APIs that require complex mocking of Redis/Celery internals."""

    def test_get_celery_status_enabled_mocked(self):
        """Test getting Celery status when enabled with proper mocking."""
        with TestClient(app) as test_client:
            # Mock the inspect object to return proper dicts
            with patch("app.services.celery.get_celery_app") as mock_get_app:
                mock_app = Mock()
                mock_inspect = Mock()
                mock_inspect.active.return_value = {
                    "worker1": [], "worker2": []}
                mock_inspect.registered.return_value = {
                    "worker1": ["task1", "task2", "task3", "task4", "task5"]}
                mock_app.control.inspect.return_value = mock_inspect
                mock_get_app.return_value = mock_app

                with patch("app.services.celery.get_celery_stats") as mock_stats:
                    mock_stats.return_value = {
                        "enabled": True,
                        "broker_url": "redis://localhost:6379/1",
                        "result_backend": "redis://localhost:6379/1",
                        "active_workers": 2,
                        "registered_tasks": 5,
                        "active_tasks": 1,
                    }

                    response = test_client.get("/api/v1/celery/status")

                    assert response.status_code == 200
                    data = response.json()
                    assert data["enabled"] is True
                    assert data["broker_url"] == "redis://localhost:6379/1"
                    assert data["result_backend"] == "redis://localhost:6379/1"
                    assert data["active_workers"] == 2
                    assert data["registered_tasks"] == 5
                    assert data["active_tasks"] == 1

    def test_get_task_status_enabled_mocked(self, client: TestClient):
        """Test getting task status when enabled with proper mocking."""
        with patch("app.services.celery.is_celery_enabled") as mock_enabled:
            mock_enabled.return_value = True

            with patch("app.api.api_v1.endpoints.celery.get_task_status") as mock_status:
                # Mock the entire function to return the expected dict
                mock_status.return_value = {
                    "task_id": "test-task-id",
                    "status": "SUCCESS",
                    "ready": True,
                    "successful": True,
                    "failed": False,
                    "result": {"status": "completed"}
                }

                response = client.get(
                    "/api/v1/celery/tasks/test-task-id/status")

                assert response.status_code == 200
                data = response.json()
                assert data["task_id"] == "test-task-id"
                assert data["status"] == "SUCCESS"
                assert data["ready"] is True
                assert data["successful"] is True
                assert data["failed"] is False
                assert data["result"] == {"status": "completed"}

    def test_get_active_tasks_enabled_mocked(self, client: TestClient):
        """Test getting active tasks when enabled with proper mocking."""
        with patch("app.services.celery.is_celery_enabled") as mock_enabled:
            mock_enabled.return_value = True

            with patch("app.services.celery.get_celery_app") as mock_get_app:
                mock_app = Mock()
                mock_inspect = Mock()
                # Return a proper dict structure that can be iterated
                mock_inspect.active.return_value = {
                    "worker1": [
                        {
                            "id": "task1",
                            "name": "send_email_task",
                            "args": ["test@example.com"],
                            "kwargs": {},
                            "time_start": 1234567890.0
                        }
                    ]
                }
                mock_app.control.inspect.return_value = mock_inspect
                mock_get_app.return_value = mock_app

                with patch("app.services.celery.get_active_tasks") as mock_active:
                    mock_active.return_value = [
                        {
                            "task_id": "task1",
                            "name": "send_email_task",
                            "worker": "worker1",
                            "args": ["test@example.com"],
                            "kwargs": {},
                            "time_start": 1234567890.0
                        }
                    ]

                    response = client.get("/api/v1/celery/tasks/active")

                    assert response.status_code == 200
                    data = response.json()
                    assert len(data) == 1
                    assert data[0]["task_id"] == "task1"
                    assert data[0]["name"] == "send_email_task"
                    assert data[0]["worker"] == "worker1"

    def test_cancel_task_enabled_success_mocked(self, client: TestClient):
        """Test cancelling a task when enabled and successful with proper mocking."""
        with patch("app.services.celery.is_celery_enabled") as mock_enabled:
            mock_enabled.return_value = True

            with patch("app.api.api_v1.endpoints.celery.cancel_task") as mock_cancel:
                mock_cancel.return_value = True

                response = client.delete(
                    "/api/v1/celery/tasks/test-task-id/cancel")

                assert response.status_code == 200
                data = response.json()
                assert data["task_id"] == "test-task-id"
                assert data["cancelled"] is True
                assert data["message"] == "Task cancelled successfully"

    def test_cancel_task_enabled_failure_mocked(self, client: TestClient):
        """Test cancelling a task when enabled but fails with proper mocking."""
        with patch("app.services.celery.is_celery_enabled") as mock_enabled:
            mock_enabled.return_value = True

            with patch("app.api.api_v1.endpoints.celery.cancel_task") as mock_cancel:
                mock_cancel.return_value = False

                response = client.delete(
                    "/api/v1/celery/tasks/test-task-id/cancel")

                assert response.status_code == 200
                data = response.json()
                assert data["task_id"] == "test-task-id"
                assert data["cancelled"] is False
                assert "Failed to cancel task" in data["message"]

    def test_get_celery_status_error_mocked(self, client: TestClient):
        """Test getting Celery status with error using proper mocking."""
        with patch("app.services.celery.is_celery_enabled") as mock_enabled:
            mock_enabled.return_value = True

            with patch("app.api.api_v1.endpoints.celery.get_celery_stats") as mock_stats:
                mock_stats.side_effect = Exception("Test error")

                response = client.get("/api/v1/celery/status")

                assert response.status_code == 500
                assert "Failed to get Celery status" in response.json()[
                    "detail"]


class TestCeleryDisabledMocked:
    """Test Celery APIs when disabled using proper dependency mocking."""

    def test_submit_celery_task_disabled_mocked(self, client: TestClient):
        """Test submitting a Celery task when disabled with proper mocking."""
        with patch("app.services.celery.is_celery_enabled") as mock_enabled:
            mock_enabled.return_value = False

            # Mock the dependency check to raise HTTPException
            with patch("app.api.api_v1.endpoints.celery.check_celery_enabled") as mock_check:
                mock_check.side_effect = HTTPException(
                    status_code=503, detail="Celery is not enabled")

                task_data = {
                    "task_name": "app.services.celery_tasks.send_email_task",
                    "args": ["test@example.com", "Test Subject", "Test Body"],
                    "kwargs": {}
                }

                response = client.post(
                    "/api/v1/celery/tasks/submit", json=task_data)

                assert response.status_code == 503
                assert "Celery is not enabled" in response.json()["detail"]

    def test_get_task_status_disabled_mocked(self, client: TestClient):
        """Test getting task status when disabled with proper mocking."""
        with patch("app.services.celery.is_celery_enabled") as mock_enabled:
            mock_enabled.return_value = False

            # Mock the dependency check to raise HTTPException
            with patch("app.api.api_v1.endpoints.celery.check_celery_enabled") as mock_check:
                mock_check.side_effect = HTTPException(
                    status_code=503, detail="Celery is not enabled")

                response = client.get(
                    "/api/v1/celery/tasks/test-task-id/status")

                assert response.status_code == 503
                assert "Celery is not enabled" in response.json()["detail"]

    def test_cancel_task_disabled_mocked(self, client: TestClient):
        """Test cancelling a task when disabled with proper mocking."""
        with patch("app.services.celery.is_celery_enabled") as mock_enabled:
            mock_enabled.return_value = False

            # Mock the dependency check to raise HTTPException
            with patch("app.api.api_v1.endpoints.celery.check_celery_enabled") as mock_check:
                mock_check.side_effect = HTTPException(
                    status_code=503, detail="Celery is not enabled")

                response = client.delete(
                    "/api/v1/celery/tasks/test-task-id/cancel")

                assert response.status_code == 503
                assert "Celery is not enabled" in response.json()["detail"]

    def test_get_active_tasks_disabled_mocked(self, client: TestClient):
        """Test getting active tasks when disabled with proper mocking."""
        with patch("app.services.celery.is_celery_enabled") as mock_enabled:
            mock_enabled.return_value = False

            # Mock the dependency check to raise HTTPException
            with patch("app.api.api_v1.endpoints.celery.check_celery_enabled") as mock_check:
                mock_check.side_effect = HTTPException(
                    status_code=503, detail="Celery is not enabled")

                response = client.get("/api/v1/celery/tasks/active")

                assert response.status_code == 503
                assert "Celery is not enabled" in response.json()["detail"]
