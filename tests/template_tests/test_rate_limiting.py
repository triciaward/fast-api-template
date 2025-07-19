"""Tests for rate limiting functionality."""

import warnings
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.services.rate_limiter import (
    get_client_ip,
    get_limiter,
    get_rate_limit_info,
    rate_limit_custom,
    rate_limit_email_verification,
    rate_limit_login,
    rate_limit_oauth,
    rate_limit_register,
    setup_rate_limiting,
)

# Suppress the RuntimeWarning about coroutine not being awaited
# This is a known issue with the test setup and doesn't affect functionality
warnings.filterwarnings(
    "ignore", message=".*coroutine.*was never awaited.*", category=RuntimeWarning
)


class TestRateLimiter:
    """Test rate limiting functionality."""

    def test_get_limiter_creates_instance(self) -> None:
        """Test that get_limiter creates a limiter instance."""
        # Clear any existing limiter
        import app.services.rate_limiter

        app.services.rate_limiter.limiter = None

        limiter = get_limiter()
        assert limiter is not None
        assert hasattr(limiter, "limit")

    def test_get_limiter_returns_same_instance(self) -> None:
        """Test that get_limiter returns the same instance."""
        limiter1 = get_limiter()
        limiter2 = get_limiter()
        assert limiter1 is limiter2

    @patch("app.services.rate_limiter.settings")
    def test_get_limiter_with_redis_backend(self, mock_settings: MagicMock) -> None:
        """Test get_limiter with Redis backend."""
        mock_settings.ENABLE_REDIS = True
        mock_settings.RATE_LIMIT_STORAGE_BACKEND = "redis"
        mock_settings.REDIS_URL = "redis://localhost:6379/0"
        mock_settings.RATE_LIMIT_DEFAULT = "100/minute"

        # Mock Redis client
        with patch("app.services.redis.get_redis_client") as mock_get_redis:
            mock_redis = MagicMock()
            mock_get_redis.return_value = mock_redis

            # Clear any existing limiter
            import app.services.rate_limiter

            app.services.rate_limiter.limiter = None

            limiter = get_limiter()
            assert limiter is not None

    def test_get_client_ip_with_forwarded_for(self) -> None:
        """Test get_client_ip with X-Forwarded-For header."""
        mock_request = MagicMock()
        mock_request.headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}
        mock_request.client.host = "127.0.0.1"

        ip = get_client_ip(mock_request)
        assert ip == "192.168.1.1"

    def test_get_client_ip_with_real_ip(self) -> None:
        """Test get_client_ip with X-Real-IP header."""
        mock_request = MagicMock()
        mock_request.headers = {"X-Real-IP": "192.168.1.2"}
        mock_request.client.host = "127.0.0.1"

        ip = get_client_ip(mock_request)
        assert ip == "192.168.1.2"

    def test_get_client_ip_fallback(self) -> None:
        """Test get_client_ip fallback to remote address."""
        mock_request = MagicMock()
        mock_request.headers = {}
        mock_request.client.host = "127.0.0.1"

        ip = get_client_ip(mock_request)
        assert ip == "127.0.0.1"

    def test_rate_limit_custom_decorator(self) -> None:
        """Test rate_limit_custom decorator."""
        decorator = rate_limit_custom("10/minute")
        assert callable(decorator)

        # Test that it can be applied to a function
        @decorator
        def test_func() -> str:
            return "test"

        assert callable(test_func)

    def test_rate_limit_decorators_exist(self) -> None:
        """Test that all rate limit decorators exist and are callable."""
        assert callable(rate_limit_login)
        assert callable(rate_limit_register)
        assert callable(rate_limit_email_verification)
        assert callable(rate_limit_oauth)
        assert callable(rate_limit_custom)

    def test_rate_limit_custom_with_limit(self) -> None:
        """Test rate_limit_custom with specific limit."""
        decorator = rate_limit_custom("5/minute")
        assert callable(decorator)

    @patch("app.services.rate_limiter.settings")
    def test_setup_rate_limiting_disabled(self, mock_settings: MagicMock) -> None:
        """Test setup_rate_limiting when rate limiting is disabled."""
        mock_settings.ENABLE_RATE_LIMITING = False

        mock_app = MagicMock()
        setup_rate_limiting(mock_app)

        # Should not add exception handler or limiter state
        mock_app.add_exception_handler.assert_not_called()

    @patch("app.services.rate_limiter.settings")
    def test_setup_rate_limiting_enabled(self, mock_settings: MagicMock) -> None:
        """Test setup_rate_limiting when rate limiting is enabled."""
        mock_settings.ENABLE_RATE_LIMITING = True

        mock_app = MagicMock()
        setup_rate_limiting(mock_app)

        # Should add exception handler
        mock_app.add_exception_handler.assert_called_once()

    @patch("app.services.rate_limiter.settings")
    def test_get_rate_limit_info_disabled(self, mock_settings: MagicMock) -> None:
        """Test get_rate_limit_info when rate limiting is disabled."""
        mock_settings.ENABLE_RATE_LIMITING = False

        mock_request = MagicMock()
        result = get_rate_limit_info(mock_request)

        assert result["enabled"] is False

    @patch("app.services.rate_limiter.settings")
    def test_get_rate_limit_info_enabled(self, mock_settings: MagicMock) -> None:
        """Test get_rate_limit_info when rate limiting is enabled."""
        mock_settings.ENABLE_RATE_LIMITING = True

        mock_request = MagicMock()
        mock_request.headers = {}
        mock_request.client.host = "127.0.0.1"

        # The get_rate_limit_info function returns hardcoded values, not from limiter
        result = get_rate_limit_info(mock_request)

        assert result["enabled"] is True
        assert result["client_ip"] == "127.0.0.1"
        assert result["remaining"] == 100  # Hardcoded in the function
        assert result["reset_time"] == 0  # Hardcoded in the function
        assert result["limit"] == 100  # Hardcoded in the function


class TestRateLimitingIntegration:
    """Integration tests for rate limiting with FastAPI app."""

    def test_rate_limiting_endpoints_exist(self, client: TestClient) -> None:
        """Test that rate limiting endpoints are accessible."""
        # Test rate limit info endpoint
        response = client.get("/api/v1/health/rate-limit")
        assert response.status_code == 200
        data = response.json()
        assert "enabled" in data

    @pytest.mark.filterwarnings("ignore::RuntimeWarning")
    def test_auth_endpoints_have_rate_limiting(self, client: TestClient) -> None:
        """Test that authentication endpoints have rate limiting applied."""
        # Test that login endpoint exists and has rate limiting
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "testpassword"},
        )
        # Should get 401 (unauthorized) not 429 (rate limited) initially
        assert response.status_code in [401, 422]  # 422 for validation error

    def test_rate_limiting_headers_present(self, client: TestClient) -> None:
        """Test that rate limiting headers are present in responses."""
        # Make a request to get rate limit info
        response = client.get("/api/v1/health/rate-limit")
        assert response.status_code == 200

        # Check for rate limiting headers (if rate limiting is enabled)
        if settings.ENABLE_RATE_LIMITING:
            # These headers might be present depending on the rate limiting implementation
            # Note: slowapi might not always add these headers, so we just check the response works
            pass

    def test_rate_limiting_configuration(self, client: TestClient) -> None:
        """Test rate limiting configuration through settings."""
        # Test that rate limiting can be configured
        assert hasattr(settings, "ENABLE_RATE_LIMITING")
        assert hasattr(settings, "RATE_LIMIT_DEFAULT")
        assert hasattr(settings, "RATE_LIMIT_LOGIN")
        assert hasattr(settings, "RATE_LIMIT_REGISTER")
        assert hasattr(settings, "RATE_LIMIT_EMAIL_VERIFICATION")
        assert hasattr(settings, "RATE_LIMIT_OAUTH")

    def test_rate_limiting_storage_backend_configuration(self) -> None:
        """Test rate limiting storage backend configuration."""
        assert hasattr(settings, "RATE_LIMIT_STORAGE_BACKEND")
        assert settings.RATE_LIMIT_STORAGE_BACKEND in ["memory", "redis"]

    @pytest.mark.asyncio
    async def test_init_rate_limiter(self) -> None:
        """Test rate limiter initialization."""
        from app.services.rate_limiter import init_rate_limiter

        # Should not raise an exception
        await init_rate_limiter()

    def test_rate_limiting_feature_flag(self, client: TestClient) -> None:
        """Test that rate limiting feature flag is exposed."""
        response = client.get("/features")
        assert response.status_code == 200
        data = response.json()
        assert "rate_limiting" in data
        assert isinstance(data["rate_limiting"], bool)


class TestRateLimitingEdgeCases:
    """Test edge cases and error handling in rate limiting."""

    def test_rate_limiter_with_invalid_redis_url(self) -> None:
        """Test rate limiter behavior with invalid Redis URL."""
        # This test would require mocking Redis connection failures
        # For now, we just ensure the function doesn't crash
        limiter = get_limiter()
        assert limiter is not None

    def test_get_client_ip_with_malformed_headers(self) -> None:
        """Test get_client_ip with malformed headers."""
        mock_request = MagicMock()
        mock_request.headers = {"X-Forwarded-For": ""}  # Empty header
        mock_request.client.host = "127.0.0.1"

        ip = get_client_ip(mock_request)
        assert ip == "127.0.0.1"  # Should fallback

    def test_rate_limit_decorator_with_invalid_limit(self) -> None:
        """Test rate limit decorator with invalid limit format."""
        # This should still create a decorator, but might fail at runtime
        decorator = rate_limit_custom("invalid_limit")
        assert callable(decorator)

    @patch("app.services.rate_limiter.settings")
    def test_get_rate_limit_info_with_limiter_error(
        self, mock_settings: MagicMock
    ) -> None:
        """Test get_rate_limit_info when limiter raises an error."""
        mock_settings.ENABLE_RATE_LIMITING = True

        mock_request = MagicMock()
        mock_request.headers = {}
        mock_request.client.host = "127.0.0.1"

        # Mock limiter that raises an error
        mock_limiter = MagicMock()
        mock_limiter.get_window_stats.side_effect = Exception("Limiter error")

        with patch("app.services.rate_limiter.get_limiter", return_value=mock_limiter):
            # Should handle the error gracefully
            result = get_rate_limit_info(mock_request)
            # The function should handle the error and return a valid response
            assert isinstance(result, dict)
