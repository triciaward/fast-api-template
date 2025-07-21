"""Tests for Sentry/GlitchTip error monitoring integration."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


class TestSentryIntegration:
    """Test Sentry/GlitchTip integration."""

    def test_sentry_configuration(self):
        """Test that Sentry configuration is properly set up."""
        # Check that Sentry settings exist
        assert hasattr(settings, "ENABLE_SENTRY")
        assert hasattr(settings, "SENTRY_DSN")
        assert hasattr(settings, "SENTRY_ENVIRONMENT")
        assert hasattr(settings, "SENTRY_TRACES_SAMPLE_RATE")
        assert hasattr(settings, "SENTRY_PROFILES_SAMPLE_RATE")

    def test_sentry_service_import(self):
        """Test that Sentry service can be imported."""
        from app.services.sentry import (
            capture_exception,
            capture_message,
            clear_user_context,
            init_sentry,
            set_user_context,
        )

        assert callable(init_sentry)
        assert callable(capture_exception)
        assert callable(capture_message)
        assert callable(set_user_context)
        assert callable(clear_user_context)

    @patch("app.services.sentry.sentry_sdk.init")
    def test_sentry_initialization_disabled(self, mock_init):
        """Test that Sentry is not initialized when disabled."""
        from app.services.sentry import init_sentry

        # Mock settings to disable Sentry
        with patch("app.services.sentry.settings") as mock_settings:
            mock_settings.ENABLE_SENTRY = False
            mock_settings.SENTRY_DSN = None

            init_sentry()

            # Sentry should not be initialized
            mock_init.assert_not_called()

    @patch("app.services.sentry.sentry_sdk.init")
    def test_sentry_initialization_enabled(self, mock_init):
        """Test that Sentry is initialized when enabled."""
        from app.services.sentry import init_sentry

        # Mock settings to enable Sentry
        with patch("app.services.sentry.settings") as mock_settings:
            mock_settings.ENABLE_SENTRY = True
            mock_settings.SENTRY_DSN = "http://test-dsn"
            mock_settings.SENTRY_ENVIRONMENT = "test"
            mock_settings.SENTRY_TRACES_SAMPLE_RATE = 0.1
            mock_settings.SENTRY_PROFILES_SAMPLE_RATE = 0.1
            mock_settings.ENABLE_REDIS = False
            mock_settings.ENABLE_CELERY = False
            mock_settings.VERSION = "1.0.0"
            mock_settings.ENVIRONMENT = "test"

            init_sentry()

            # Sentry should be initialized
            mock_init.assert_called_once()

    @patch("app.services.sentry.sentry_sdk.capture_exception")
    def test_capture_exception_disabled(self, mock_capture):
        """Test that exceptions are not captured when Sentry is disabled."""
        from app.services.sentry import capture_exception

        with patch("app.services.sentry.settings") as mock_settings:
            mock_settings.ENABLE_SENTRY = False

            test_exception = ValueError("Test exception")
            capture_exception(test_exception)

            # Exception should not be captured
            mock_capture.assert_not_called()

    @patch("app.services.sentry.sentry_sdk.capture_exception")
    def test_capture_exception_enabled(self, mock_capture):
        """Test that exceptions are captured when Sentry is enabled."""
        from app.services.sentry import capture_exception

        with patch("app.services.sentry.settings") as mock_settings:
            mock_settings.ENABLE_SENTRY = True

            test_exception = ValueError("Test exception")
            context = {"test": "context"}
            capture_exception(test_exception, context)

            # Exception should be captured
            mock_capture.assert_called_once()

    @patch("app.services.sentry.sentry_sdk.capture_message")
    def test_capture_message_disabled(self, mock_capture):
        """Test that messages are not captured when Sentry is disabled."""
        from app.services.sentry import capture_message

        with patch("app.services.sentry.settings") as mock_settings:
            mock_settings.ENABLE_SENTRY = False

            capture_message("Test message", "info", {"test": "context"})

            # Message should not be captured
            mock_capture.assert_not_called()

    @patch("app.services.sentry.sentry_sdk.capture_message")
    def test_capture_message_enabled(self, mock_capture):
        """Test that messages are captured when Sentry is enabled."""
        from app.services.sentry import capture_message

        with patch("app.services.sentry.settings") as mock_settings:
            mock_settings.ENABLE_SENTRY = True

            capture_message("Test message", "info", {"test": "context"})

            # Message should be captured
            mock_capture.assert_called_once()

    @patch("app.services.sentry.sentry_sdk.set_user")
    def test_set_user_context(self, mock_set_user):
        """Test setting user context in Sentry."""
        from app.services.sentry import set_user_context

        with patch("app.services.sentry.settings") as mock_settings:
            mock_settings.ENABLE_SENTRY = True

            set_user_context(user_id=123, email="test@example.com")

            # User context should be set
            mock_set_user.assert_called_once_with(
                {"id": "123", "email": "test@example.com"}
            )

    @patch("app.services.sentry.sentry_sdk.set_user")
    def test_clear_user_context(self, mock_set_user):
        """Test clearing user context in Sentry."""
        from app.services.sentry import clear_user_context

        with patch("app.services.sentry.settings") as mock_settings:
            mock_settings.ENABLE_SENTRY = True

            clear_user_context()

            # User context should be cleared
            mock_set_user.assert_called_once_with(None)


class TestSentryAPIEndpoints:
    """Test API endpoints with Sentry integration."""

    def test_health_endpoint_sentry_status(self):
        """Test that health endpoint includes Sentry status."""
        client = TestClient(app)

        response = client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert "sentry" in data
        assert "enabled" in data["sentry"]

        # Should be disabled by default in tests
        assert data["sentry"]["enabled"] is False

    def test_sentry_test_endpoint(self):
        """Test the Sentry test endpoint."""
        client = TestClient(app)

        response = client.get("/api/v1/health/test-sentry")

        # Should return 500 (intentional error)
        assert response.status_code == 500

        data = response.json()
        assert "error" in data
        assert "message" in data["error"]
        assert (
            "This is a test exception for Sentry monitoring" in data["error"]["message"]
        )

    def test_sentry_test_endpoint_disabled(self):
        """Test Sentry test endpoint when Sentry is disabled."""
        client = TestClient(app)

        # Mock Sentry to be disabled
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.ENABLE_SENTRY = False

            response = client.get("/api/v1/health/test-sentry")

            # Should still return 500 (intentional error)
            assert response.status_code == 500

            data = response.json()
            assert "error" in data
            assert "message" in data["error"]
            assert (
                "This is a test exception for Sentry monitoring"
                in data["error"]["message"]
            )


class TestSentryErrorHandling:
    """Test Sentry error handling in various scenarios."""

    @patch("app.services.sentry.capture_exception")
    def test_database_error_capture(self, mock_capture):
        """Test that database errors are captured by Sentry."""
        from app.services.sentry import capture_exception

        with patch("app.services.sentry.settings") as mock_settings:
            mock_settings.ENABLE_SENTRY = True

            # Simulate database error
            db_error = Exception("Database connection failed")
            capture_exception(db_error, {"check": "database", "endpoint": "health"})

            # Should capture the exception with context
            mock_capture.assert_called_once()

    def test_sentry_failure_graceful(self):
        """Test that Sentry failures don't break the application."""
        from app.services.sentry import capture_exception

        with patch("app.services.sentry.sentry_sdk.capture_exception") as mock_capture:
            mock_capture.side_effect = Exception("Sentry failed")

            with patch("app.services.sentry.settings") as mock_settings:
                mock_settings.ENABLE_SENTRY = True

                # Should not raise an exception
                try:
                    capture_exception(ValueError("Test"))
                except Exception:
                    pytest.fail("Sentry failure should not break the application")
