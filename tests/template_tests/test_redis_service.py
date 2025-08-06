"""
Tests for Redis service.

This module tests the Redis service functionality including connection, health checks, and error handling.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import redis.asyncio as redis

from app.services.redis import (
    init_redis,
    close_redis,
    get_redis_client,
    health_check_redis,
    redis_client,
)


class TestRedisService:
    """Test Redis service functionality."""

    @patch("app.services.redis.settings")
    @patch("app.services.redis.redis.from_url")
    async def test_init_redis_success(self, mock_redis_from_url, mock_settings):
        """Test successful Redis initialization."""
        # Mock settings
        mock_settings.ENABLE_REDIS = True
        mock_settings.REDIS_URL = "redis://localhost:6379"

        # Mock Redis client
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock()
        mock_redis_from_url.return_value = mock_client

        # Test initialization
        result = await init_redis()

        # Verify Redis client was created
        mock_redis_from_url.assert_called_once_with(
            "redis://localhost:6379",
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )

        # Verify ping was called
        mock_client.ping.assert_called_once()

        # Verify result
        assert result == mock_client

    @patch("app.services.redis.settings")
    async def test_init_redis_disabled(self, mock_settings):
        """Test Redis initialization when disabled."""
        # Mock settings
        mock_settings.ENABLE_REDIS = False

        # Test initialization
        result = await init_redis()

        # Verify result is None
        assert result is None

    @patch("app.services.redis.settings")
    @patch("app.services.redis.redis.from_url")
    async def test_init_redis_connection_error(self, mock_redis_from_url, mock_settings):
        """Test Redis initialization with connection error."""
        # Mock settings
        mock_settings.ENABLE_REDIS = True
        mock_settings.REDIS_URL = "redis://localhost:6379"

        # Mock Redis client to raise exception
        mock_redis_from_url.side_effect = Exception("Connection failed")

        # Test initialization
        result = await init_redis()

        # Verify result is None
        assert result is None

    @patch("app.services.redis.settings")
    @patch("app.services.redis.redis.from_url")
    async def test_init_redis_ping_error(self, mock_redis_from_url, mock_settings):
        """Test Redis initialization with ping error."""
        # Mock settings
        mock_settings.ENABLE_REDIS = True
        mock_settings.REDIS_URL = "redis://localhost:6379"

        # Mock Redis client
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(side_effect=Exception("Ping failed"))
        mock_redis_from_url.return_value = mock_client

        # Test initialization
        result = await init_redis()

        # Verify result is None
        assert result is None

    async def test_close_redis_success(self):
        """Test successful Redis connection closure."""
        # Mock Redis client
        mock_client = AsyncMock()
        mock_client.close = AsyncMock()
        
        # Temporarily set the global client
        import app.services.redis as redis_module
        original_client = redis_module.redis_client
        redis_module.redis_client = mock_client

        try:
            # Test closure
            await close_redis()

            # Verify close was called
            mock_client.close.assert_called_once()
        finally:
            # Restore original client
            redis_module.redis_client = original_client

    async def test_close_redis_error(self):
        """Test Redis connection closure with error."""
        # Mock Redis client
        mock_client = AsyncMock()
        mock_client.close = AsyncMock(side_effect=Exception("Close failed"))
        
        # Temporarily set the global client
        import app.services.redis as redis_module
        original_client = redis_module.redis_client
        redis_module.redis_client = mock_client

        try:
            # Test closure (should not raise exception)
            await close_redis()

            # Verify close was called
            mock_client.close.assert_called_once()
        finally:
            # Restore original client
            redis_module.redis_client = original_client

    @patch("app.services.redis.redis_client")
    async def test_close_redis_no_client(self, mock_redis_client):
        """Test Redis connection closure when no client exists."""
        # Mock no Redis client
        mock_redis_client = None

        # Test closure (should not raise exception)
        await close_redis()

    def test_get_redis_client_with_client(self):
        """Test getting Redis client when available."""
        # Mock Redis client
        mock_client = MagicMock()
        
        # Temporarily set the global client
        import app.services.redis as redis_module
        original_client = redis_module.redis_client
        redis_module.redis_client = mock_client

        try:
            # Test getting client
            result = get_redis_client()

            # Verify result
            assert result == mock_client
        finally:
            # Restore original client
            redis_module.redis_client = original_client

    def test_get_redis_client_no_client(self):
        """Test getting Redis client when not available."""
        # Mock no Redis client
        import app.services.redis as redis_module
        original_client = redis_module.redis_client
        redis_module.redis_client = None

        try:
            # Test getting client
            result = get_redis_client()

            # Verify result
            assert result is None
        finally:
            # Restore original client
            redis_module.redis_client = original_client

    async def test_health_check_redis_success(self):
        """Test successful Redis health check."""
        # Mock Redis client
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock()
        
        # Temporarily set the global client
        import app.services.redis as redis_module
        original_client = redis_module.redis_client
        redis_module.redis_client = mock_client

        try:
            # Test health check
            result = await health_check_redis()

            # Verify result
            assert result is True

            # Verify ping was called
            mock_client.ping.assert_called_once()
        finally:
            # Restore original client
            redis_module.redis_client = original_client

    @patch("app.services.redis.redis_client")
    async def test_health_check_redis_no_client(self, mock_redis_client):
        """Test Redis health check when no client exists."""
        # Mock no Redis client
        mock_redis_client = None

        # Test health check
        result = await health_check_redis()

        # Verify result
        assert result is False

    async def test_health_check_redis_error(self):
        """Test Redis health check with error."""
        # Mock Redis client
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(side_effect=Exception("Health check failed"))
        
        # Temporarily set the global client
        import app.services.redis as redis_module
        original_client = redis_module.redis_client
        redis_module.redis_client = mock_client

        try:
            # Test health check
            result = await health_check_redis()

            # Verify result
            assert result is False

            # Verify ping was called
            mock_client.ping.assert_called_once()
        finally:
            # Restore original client
            redis_module.redis_client = original_client


class TestRedisServiceIntegration:
    """Test Redis service integration scenarios."""

    @patch("app.services.redis.settings")
    @patch("app.services.redis.redis.from_url")
    async def test_redis_lifecycle(self, mock_redis_from_url, mock_settings):
        """Test complete Redis lifecycle: init -> health check -> close."""
        # Mock settings
        mock_settings.ENABLE_REDIS = True
        mock_settings.REDIS_URL = "redis://localhost:6379"

        # Mock Redis client
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock()
        mock_client.close = AsyncMock()
        mock_redis_from_url.return_value = mock_client

        # Test initialization
        result = await init_redis()
        assert result == mock_client

        # Test health check
        health_result = await health_check_redis()
        assert health_result is True

        # Test closure
        await close_redis()
        mock_client.close.assert_called_once()

    @patch("app.services.redis.settings")
    async def test_redis_disabled_lifecycle(self, mock_settings):
        """Test Redis lifecycle when Redis is disabled."""
        # Mock settings
        mock_settings.ENABLE_REDIS = False

        # Test initialization
        result = await init_redis()
        assert result is None

        # Test health check
        health_result = await health_check_redis()
        assert health_result is False

        # Test closure (should not raise exception)
        await close_redis()

        # Test getting client
        client_result = get_redis_client()
        assert client_result is None 