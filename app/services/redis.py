"""
Redis service module for optional Redis integration.

This module provides Redis functionality that is only loaded when ENABLE_REDIS=true.
Redis connection is globally available for use in background tasks and other services.
"""

import logging

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global Redis client instance
redis_client: redis.Redis | None = None


async def init_redis() -> redis.Redis | None:
    """
    Initialize Redis connection if enabled.

    Returns:
        Redis client instance if enabled, None otherwise
    """
    global redis_client

    if not settings.ENABLE_REDIS:
        logger.info("Redis is disabled. Skipping Redis initialization.")
        return None

    try:
        logger.info(f"Initializing Redis connection to {settings.REDIS_URL}")
        redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )

        # Test the connection
        await redis_client.ping()
        logger.info("Redis connection established successfully")
        return redis_client

    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")
        redis_client = None
        return None


async def close_redis() -> None:
    """Close Redis connection if it exists."""
    global redis_client

    if redis_client:
        try:
            await redis_client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
        finally:
            redis_client = None


def get_redis_client() -> redis.Redis | None:
    """
    Get the global Redis client instance.

    Returns:
        Redis client instance if available, None otherwise
    """
    return redis_client


async def health_check_redis() -> bool:
    """
    Check Redis health by attempting to ping the server.

    Returns:
        True if Redis is healthy, False otherwise
    """
    if not redis_client:
        return False

    try:
        await redis_client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False
