"""Comprehensive rate limiter tests with various backends and configurations."""
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Request
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded

from app.services.middleware.rate_limiter import (
    get_client_ip,
    get_limiter,
    get_rate_limit_info,
    rate_limit_custom,
    rate_limit_email_verification,
    rate_limit_login,
    rate_limit_oauth,
    rate_limit_password_reset,
    rate_limit_register,
    setup_rate_limiting,
)

pytestmark = pytest.mark.unit


class TestRateLimiterConfiguration:
    """Test rate limiter configuration with different backends."""

    def test_get_limiter_memory_backend(self, monkeypatch):
        """Test limiter creation with memory backend."""
        # Clear any existing limiter
        from app.services.middleware import rate_limiter
        rate_limiter.limiter = None

        monkeypatch.setattr("app.core.config.settings.ENABLE_REDIS", False)
        monkeypatch.setattr("app.core.config.settings.RATE_LIMIT_STORAGE_BACKEND", "memory")
        monkeypatch.setattr("app.core.config.settings.RATE_LIMIT_DEFAULT", "100/hour")

        limiter = get_limiter()

        assert isinstance(limiter, Limiter)
        assert limiter is not None

    def test_get_limiter_redis_backend_configured(self, monkeypatch):
        """Test limiter creation with Redis backend when Redis is available."""
        # Clear any existing limiter
        from app.services.middleware import rate_limiter
        rate_limiter.limiter = None

        monkeypatch.setattr("app.core.config.settings.ENABLE_REDIS", True)
        monkeypatch.setattr("app.core.config.settings.RATE_LIMIT_STORAGE_BACKEND", "redis")
        monkeypatch.setattr("app.core.config.settings.REDIS_URL", "redis://localhost:6379")
        monkeypatch.setattr("app.core.config.settings.RATE_LIMIT_DEFAULT", "100/hour")

        # Mock Redis client as available
        with patch("app.services.external.redis.get_redis_client") as mock_get_redis:
            mock_redis_client = MagicMock()
            mock_get_redis.return_value = mock_redis_client

            limiter = get_limiter()

            assert isinstance(limiter, Limiter)
            mock_get_redis.assert_called_once()

    def test_get_limiter_redis_backend_fallback_to_memory(self, monkeypatch):
        """Test fallback to memory when Redis backend is configured but unavailable."""
        # Clear any existing limiter
        from app.services.middleware import rate_limiter
        rate_limiter.limiter = None

        monkeypatch.setattr("app.core.config.settings.ENABLE_REDIS", True)
        monkeypatch.setattr("app.core.config.settings.RATE_LIMIT_STORAGE_BACKEND", "redis")
        monkeypatch.setattr("app.core.config.settings.RATE_LIMIT_DEFAULT", "100/hour")

        # Mock Redis client as unavailable
        with patch("app.services.external.redis.get_redis_client") as mock_get_redis:
            mock_get_redis.return_value = None

            limiter = get_limiter()

            assert isinstance(limiter, Limiter)
            mock_get_redis.assert_called_once()

    def test_get_limiter_singleton_behavior(self, monkeypatch):
        """Test that get_limiter returns the same instance (singleton pattern)."""
        # Clear any existing limiter
        from app.services.middleware import rate_limiter
        rate_limiter.limiter = None

        monkeypatch.setattr("app.core.config.settings.ENABLE_REDIS", False)
        monkeypatch.setattr("app.core.config.settings.RATE_LIMIT_DEFAULT", "100/hour")

        limiter1 = get_limiter()
        limiter2 = get_limiter()

        assert limiter1 is limiter2


class TestClientIPExtraction:
    """Test client IP extraction with various proxy configurations."""

    def test_get_client_ip_direct_connection(self):
        """Test IP extraction for direct connections."""
        request = MagicMock(spec=Request)
        request.client.host = "192.168.1.100"
        request.headers = {}

        client_ip = get_client_ip(request)

        assert client_ip == "192.168.1.100"

    def test_get_client_ip_with_x_forwarded_for(self):
        """Test IP extraction with X-Forwarded-For header."""
        request = MagicMock(spec=Request)
        request.client.host = "10.0.0.1"  # Load balancer IP
        request.headers = {"X-Forwarded-For": "203.0.113.1, 198.51.100.1"}

        client_ip = get_client_ip(request)

        assert client_ip == "203.0.113.1"  # First IP in the chain

    def test_get_client_ip_with_x_real_ip(self):
        """Test IP extraction with X-Real-IP header."""
        request = MagicMock(spec=Request)
        request.client.host = "10.0.0.1"
        request.headers = {"X-Real-IP": "203.0.113.1"}

        client_ip = get_client_ip(request)

        assert client_ip == "203.0.113.1"

    def test_get_client_ip_fallback_to_remote_address(self):
        """Test fallback to remote address when no proxy headers."""
        request = MagicMock(spec=Request)
        request.client.host = "203.0.113.1"
        request.headers = {}

        with patch("app.services.middleware.rate_limiter.get_remote_address") as mock_get_remote:
            mock_get_remote.return_value = "203.0.113.1"

            client_ip = get_client_ip(request)

            assert client_ip == "203.0.113.1"

    def test_get_client_ip_priority_order(self):
        """Test that headers are checked in correct priority order."""
        request = MagicMock(spec=Request)
        request.client.host = "10.0.0.1"
        request.headers = {
            "X-Forwarded-For": "203.0.113.1",
            "X-Real-IP": "198.51.100.1",
        }

        client_ip = get_client_ip(request)

        # X-Forwarded-For should have highest priority
        assert client_ip == "203.0.113.1"

    def test_get_client_ip_remote_address_fallback(self):
        """Test fallback to get_remote_address when no headers present."""
        request = MagicMock(spec=Request)
        request.headers = {}

        with patch("app.services.middleware.rate_limiter.get_remote_address") as mock_get_remote:
            mock_get_remote.return_value = "192.168.1.100"

            client_ip = get_client_ip(request)

            assert client_ip == "192.168.1.100"
            mock_get_remote.assert_called_once_with(request)


class TestRateLimitDecorators:
    """Test rate limiting decorators."""

    def test_rate_limit_login_enabled(self, monkeypatch):
        """Test login rate limiting when enabled."""
        monkeypatch.setattr("app.core.config.settings.ENABLE_RATE_LIMITING", True)
        monkeypatch.setattr("app.core.config.settings.RATE_LIMIT_LOGIN", "5/minute")

        def dummy_function(request: Request):
            return "success"

        with patch("app.services.middleware.rate_limiter.get_limiter") as mock_get_limiter:
            mock_limiter = MagicMock()
            # The limiter.limit(rate) returns a decorator function, which when called with func, returns the decorated function
            mock_limiter.limit.return_value = lambda f: f  # Mock decorator that just returns the original function
            mock_get_limiter.return_value = mock_limiter

            decorated_func = rate_limit_login(dummy_function)

            mock_limiter.limit.assert_called_once_with("5/minute")
            assert decorated_func == dummy_function

    def test_rate_limit_login_disabled(self, monkeypatch):
        """Test login rate limiting when disabled."""
        monkeypatch.setattr("app.core.config.settings.ENABLE_RATE_LIMITING", False)

        def dummy_function(request: Request):
            return "success"

        decorated_func = rate_limit_login(dummy_function)
        from unittest.mock import MagicMock
        mock_request = MagicMock()
        result = decorated_func(mock_request)

        assert result == "success"
        assert decorated_func == dummy_function

    def test_rate_limit_register_enabled(self, monkeypatch):
        """Test register rate limiting when enabled."""
        monkeypatch.setattr("app.core.config.settings.ENABLE_RATE_LIMITING", True)
        monkeypatch.setattr("app.core.config.settings.RATE_LIMIT_REGISTER", "3/hour")

        def dummy_function(request: Request):
            return "registered"

        with patch("app.services.middleware.rate_limiter.get_limiter") as mock_get_limiter:
            mock_limiter = MagicMock()
            mock_limiter.limit.return_value = lambda f: f  # Mock decorator that returns the original function
            mock_get_limiter.return_value = mock_limiter

            decorated_func = rate_limit_register(dummy_function)

            mock_limiter.limit.assert_called_once_with("3/hour")

    def test_rate_limit_email_verification_enabled(self, monkeypatch):
        """Test email verification rate limiting when enabled."""
        monkeypatch.setattr("app.core.config.settings.ENABLE_RATE_LIMITING", True)
        monkeypatch.setattr("app.core.config.settings.RATE_LIMIT_EMAIL_VERIFICATION", "2/minute")

        def dummy_function(request: Request):
            return "verified"

        with patch("app.services.middleware.rate_limiter.get_limiter") as mock_get_limiter:
            mock_limiter = MagicMock()
            mock_limiter.limit.return_value = lambda f: f  # Mock decorator that returns the original function
            mock_get_limiter.return_value = mock_limiter

            decorated_func = rate_limit_email_verification(dummy_function)

            mock_limiter.limit.assert_called_once_with("2/minute")

    def test_rate_limit_password_reset_enabled(self, monkeypatch):
        """Test password reset rate limiting when enabled."""
        monkeypatch.setattr("app.core.config.settings.ENABLE_RATE_LIMITING", True)
        monkeypatch.setattr("app.core.config.settings.RATE_LIMIT_PASSWORD_RESET", "1/minute")

        def dummy_function(request: Request):
            return "reset"

        with patch("app.services.middleware.rate_limiter.get_limiter") as mock_get_limiter:
            mock_limiter = MagicMock()
            mock_limiter.limit.return_value = lambda f: f  # Mock decorator that returns the original function
            mock_get_limiter.return_value = mock_limiter

            decorated_func = rate_limit_password_reset(dummy_function)

            mock_limiter.limit.assert_called_once_with("1/minute")

    def test_rate_limit_oauth_enabled(self, monkeypatch):
        """Test OAuth rate limiting when enabled."""
        monkeypatch.setattr("app.core.config.settings.ENABLE_RATE_LIMITING", True)
        monkeypatch.setattr("app.core.config.settings.RATE_LIMIT_OAUTH", "10/minute")

        def dummy_function(request: Request):
            return "oauth_success"

        with patch("app.services.middleware.rate_limiter.get_limiter") as mock_get_limiter:
            mock_limiter = MagicMock()
            mock_limiter.limit.return_value = lambda f: f  # Mock decorator that returns the original function
            mock_get_limiter.return_value = mock_limiter

            decorated_func = rate_limit_oauth(dummy_function)

            mock_limiter.limit.assert_called_once_with("10/minute")

    def test_rate_limit_custom_enabled(self, monkeypatch):
        """Test custom rate limiting when enabled."""
        monkeypatch.setattr("app.core.config.settings.ENABLE_RATE_LIMITING", True)

        def dummy_function(request: Request):
            return "custom"

        with patch("app.services.middleware.rate_limiter.get_limiter") as mock_get_limiter:
            mock_limiter = MagicMock()
            mock_limiter.limit.return_value = lambda f: f  # Mock decorator that returns the original function
            mock_get_limiter.return_value = mock_limiter

            decorator = rate_limit_custom("5/second")
            decorated_func = decorator(dummy_function)

            mock_limiter.limit.assert_called_once_with("5/second")

    def test_rate_limit_custom_disabled(self, monkeypatch):
        """Test custom rate limiting when disabled."""
        monkeypatch.setattr("app.core.config.settings.ENABLE_RATE_LIMITING", False)

        def dummy_function():
            return "custom"

        decorator = rate_limit_custom("5/second")
        decorated_func = decorator(dummy_function)
        result = decorated_func()

        assert result == "custom"
        assert decorated_func == dummy_function


class TestRateLimitInfo:
    """Test rate limit information retrieval."""

    def test_get_rate_limit_info_disabled(self, monkeypatch):
        """Test rate limit info when rate limiting is disabled."""
        monkeypatch.setattr("app.core.config.settings.ENABLE_RATE_LIMITING", False)

        request = MagicMock(spec=Request)

        info = get_rate_limit_info(request)

        assert info == {"enabled": False}

    def test_get_rate_limit_info_enabled_success(self, monkeypatch):
        """Test rate limit info when rate limiting is enabled and working."""
        monkeypatch.setattr("app.core.config.settings.ENABLE_RATE_LIMITING", True)

        request = MagicMock(spec=Request)
        request.client.host = "192.168.1.100"
        request.headers = {}

        info = get_rate_limit_info(request)

        assert info["enabled"] is True
        assert info["client_ip"] == "192.168.1.100"
        assert "remaining" in info
        assert "reset_time" in info
        assert "limit" in info

    def test_get_rate_limit_info_enabled_error(self, monkeypatch):
        """Test rate limit info when rate limiting is enabled but there's an error."""
        # Import the settings to patch them correctly
        from app.services.middleware.rate_limiter import settings
        monkeypatch.setattr(settings, "ENABLE_RATE_LIMITING", True)

        # Mock get_client_ip to raise an exception
        def mock_get_client_ip(request):
            raise Exception("Network error")

        from app.services.middleware import rate_limiter
        monkeypatch.setattr(rate_limiter, "get_client_ip", mock_get_client_ip)

        request = MagicMock(spec=Request)
        request.client = MagicMock()
        request.client.host = "192.168.1.100"
        request.headers = {}

        info = get_rate_limit_info(request)

        assert info["enabled"] is True
        assert info["error"] == "Failed to get rate limit information"
        assert info["client_ip"] == "192.168.1.100"
        assert info["remaining"] == 0


class TestSetupRateLimiting:
    """Test rate limiting setup for FastAPI app."""

    def test_setup_rate_limiting_enabled(self, monkeypatch):
        """Test setting up rate limiting when enabled."""
        monkeypatch.setattr("app.core.config.settings.ENABLE_RATE_LIMITING", True)

        mock_app = MagicMock()
        mock_app.state = MagicMock()

        with patch("app.services.middleware.rate_limiter.get_limiter") as mock_get_limiter:
            mock_limiter = MagicMock()
            mock_get_limiter.return_value = mock_limiter

            setup_rate_limiting(mock_app)

            mock_get_limiter.assert_called_once()
            assert mock_app.state.limiter == mock_limiter

    def test_setup_rate_limiting_disabled(self, monkeypatch):
        """Test setting up rate limiting when disabled."""
        monkeypatch.setattr("app.core.config.settings.ENABLE_RATE_LIMITING", False)

        mock_app = MagicMock()

        setup_rate_limiting(mock_app)

        # Should return early without setting up anything
        mock_app.add_exception_handler.assert_not_called()


class TestRateLimitExceptionHandling:
    """Test rate limit exception handling scenarios."""

    def test_rate_limit_exceeded_response_format(self, monkeypatch):
        """Test that rate limit exceeded exceptions contain proper information."""
        monkeypatch.setattr("app.core.config.settings.ENABLE_RATE_LIMITING", True)

        # Create a mock Limit object that RateLimitExceeded expects
        from unittest.mock import MagicMock
        mock_limit = MagicMock()
        mock_limit.limit = "5 per 1 minute"
        mock_limit.error_message = "Rate limit exceeded"

        # This test verifies the exception structure that would be caught by FastAPI
        exception = RateLimitExceeded(mock_limit)

        assert hasattr(exception, "detail")
        assert exception.limit == mock_limit

    def test_multiple_decorators_compatibility(self, monkeypatch):
        """Test that multiple rate limiting decorators can be applied to the same function."""
        monkeypatch.setattr("app.core.config.settings.ENABLE_RATE_LIMITING", False)

        def dummy_function(request: Request):
            return "success"

        # Apply multiple decorators
        decorated_func = rate_limit_login(
            rate_limit_register(
                rate_limit_email_verification(dummy_function),
            ),
        )

        from unittest.mock import MagicMock
        mock_request = MagicMock()
        result = decorated_func(mock_request)
        assert result == "success"


class TestRateLimitIntegration:
    """Integration tests for rate limiting with various scenarios."""

    def test_rate_limiter_with_different_ips(self, monkeypatch):
        """Test that rate limiting tracks different IPs separately."""
        monkeypatch.setattr("app.core.config.settings.ENABLE_RATE_LIMITING", True)

        request1 = MagicMock(spec=Request)
        request1.client.host = "192.168.1.100"
        request1.headers = {}

        request2 = MagicMock(spec=Request)
        request2.client.host = "192.168.1.101"
        request2.headers = {}

        ip1 = get_client_ip(request1)
        ip2 = get_client_ip(request2)

        assert ip1 != ip2
        assert ip1 == "192.168.1.100"
        assert ip2 == "192.168.1.101"

    def test_rate_limiter_environment_configuration(self, monkeypatch):
        """Test that rate limiter respects environment configuration."""
        # Test with different rate limit values
        monkeypatch.setattr("app.core.config.settings.RATE_LIMIT_LOGIN", "10/minute")
        monkeypatch.setattr("app.core.config.settings.RATE_LIMIT_REGISTER", "5/hour")

        # Clear limiter to force recreation with new settings
        from app.services.middleware import rate_limiter
        rate_limiter.limiter = None

        monkeypatch.setattr("app.core.config.settings.ENABLE_RATE_LIMITING", True)
        monkeypatch.setattr("app.core.config.settings.RATE_LIMIT_DEFAULT", "100/hour")

        def dummy_login(request: Request):
            return "login"

        def dummy_register(request: Request):
            return "register"

        with patch("app.services.middleware.rate_limiter.get_limiter") as mock_get_limiter:
            mock_limiter = MagicMock()
            mock_limiter.limit.return_value = lambda x: x  # Return the original function
            mock_get_limiter.return_value = mock_limiter

            rate_limit_login(dummy_login)
            rate_limit_register(dummy_register)

            # Verify the correct rate limits were used
            calls = mock_limiter.limit.call_args_list
            assert len(calls) == 2
            assert calls[0][0][0] == "10/minute"  # Login rate limit
            assert calls[1][0][0] == "5/hour"     # Register rate limit
