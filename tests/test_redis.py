"""
Unit tests for Redis service module.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.redis import (
    close_redis,
    get_redis_client,
    health_check_redis,
    init_redis,
)


class TestRedisService:
    """Test Redis service functionality."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Setup test environment."""
        # Reset Redis client before each test
        import app.services.redis

        app.services.redis.redis_client = None

    @patch("app.services.redis.settings")
    @patch("app.services.redis.redis")
    async def test_init_redis_disabled(
        self, mock_redis: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test Redis initialization when disabled."""
        mock_settings.ENABLE_REDIS = False

        result = await init_redis()

        assert result is None
        mock_redis.from_url.assert_not_called()

    @patch("app.services.redis.settings")
    @patch("app.services.redis.redis")
    async def test_init_redis_success(
        self, mock_redis: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test successful Redis initialization."""
        mock_settings.ENABLE_REDIS = True
        mock_settings.REDIS_URL = "redis://localhost:6379/0"

        mock_client = AsyncMock()
        mock_redis.from_url.return_value = mock_client
        mock_client.ping.return_value = True

        result = await init_redis()

        assert result == mock_client
        mock_redis.from_url.assert_called_once_with(
            "redis://localhost:6379/0",
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
        mock_client.ping.assert_called_once()

    @patch("app.services.redis.settings")
    @patch("app.services.redis.redis")
    async def test_init_redis_connection_error(
        self, mock_redis: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test Redis initialization with connection error."""
        mock_settings.ENABLE_REDIS = True
        mock_settings.REDIS_URL = "redis://localhost:6379/0"

        mock_redis.from_url.side_effect = Exception("Connection failed")

        result = await init_redis()

        assert result is None

    @patch("app.services.redis.settings")
    @patch("app.services.redis.redis")
    async def test_init_redis_ping_error(
        self, mock_redis: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test Redis initialization with ping error."""
        mock_settings.ENABLE_REDIS = True
        mock_settings.REDIS_URL = "redis://localhost:6379/0"

        mock_client = AsyncMock()
        mock_redis.from_url.return_value = mock_client
        mock_client.ping.side_effect = Exception("Ping failed")

        result = await init_redis()

        assert result is None

    async def test_close_redis_no_client(self) -> None:
        """Test closing Redis when no client exists."""
        # Ensure no client exists
        import app.services.redis

        app.services.redis.redis_client = None

        await close_redis()
        # Should not raise any exceptions

    @patch("app.services.redis.redis_client")
    async def test_close_redis_success(self, mock_redis_client: MagicMock) -> None:
        """Test successful Redis connection closure."""
        mock_client = AsyncMock()
        mock_redis_client.__class__ = mock_client.__class__
        mock_redis_client.close = mock_client.close

        await close_redis()

        mock_client.close.assert_called_once()

    @patch("app.services.redis.redis_client")
    async def test_close_redis_error(self, mock_redis_client: MagicMock) -> None:
        """Test Redis closure with error."""
        mock_client = AsyncMock()
        mock_client.close.side_effect = Exception("Close failed")
        mock_redis_client.__class__ = mock_client.__class__
        mock_redis_client.close = mock_client.close

        await close_redis()
        # Should not raise exception

    def test_get_redis_client_none(self) -> None:
        """Test getting Redis client when none exists."""
        # Ensure no client exists
        import app.services.redis

        app.services.redis.redis_client = None

        result = get_redis_client()
        assert result is None

    def test_get_redis_client_exists(self) -> None:
        """Test getting existing Redis client."""
        mock_client = MagicMock()
        import app.services.redis

        app.services.redis.redis_client = mock_client

        result = get_redis_client()
        assert result == mock_client

    async def test_health_check_redis_no_client(self) -> None:
        """Test Redis health check when no client exists."""
        # Ensure no client exists
        import app.services.redis

        app.services.redis.redis_client = None

        result = await health_check_redis()
        assert result is False

    @patch("app.services.redis.redis_client")
    async def test_health_check_redis_success(
        self, mock_redis_client: MagicMock
    ) -> None:
        """Test successful Redis health check."""
        mock_client = AsyncMock()
        mock_client.ping.return_value = True
        mock_redis_client.__class__ = mock_client.__class__
        mock_redis_client.ping = mock_client.ping

        result = await health_check_redis()
        assert result is True
        mock_client.ping.assert_called_once()

    @patch("app.services.redis.redis_client")
    async def test_health_check_redis_error(self, mock_redis_client: MagicMock) -> None:
        """Test Redis health check with error."""
        mock_client = AsyncMock()
        mock_client.ping.side_effect = Exception("Health check failed")
        mock_redis_client.__class__ = mock_client.__class__
        mock_redis_client.ping = mock_client.ping

        result = await health_check_redis()
        assert result is False
