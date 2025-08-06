"""
Health check endpoints for monitoring application status.

This module provides comprehensive health checks for:
- Application status
- Database connectivity
- Redis connectivity (if enabled)
- External service dependencies
- System resources
"""

import time
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging_config import get_app_logger
from app.database.database import get_db_sync

router = APIRouter()
logger = get_app_logger()


@router.get("/health")
async def health_check(db: Session = Depends(get_db_sync)) -> dict[str, Any]:
    """
    Basic health check endpoint.

    Returns:
        dict: Application status information
    """
    health_status: dict[str, Any] = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": {
            "database": "unknown",
            "application": "healthy",
            "external_services": "unknown",
        },
        "sentry": {
            "enabled": settings.ENABLE_SENTRY,
        },
    }

    # Only include Redis check if Redis is enabled
    if settings.ENABLE_REDIS:
        health_status["checks"]["redis"] = "unknown"

    # Database connectivity check
    try:
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        health_status["checks"]["database"] = "healthy"
        logger.debug("Database health check passed")

        # Add database pool metrics if database is healthy
        try:
            from app.database.database import engine, sync_engine

            # Get sync pool metrics
            sync_pool = sync_engine.pool
            health_status["database_pools"] = {
                "sync": {
                    "size": getattr(sync_pool, "size", lambda: 0)(),
                    "checked_in": getattr(sync_pool, "checkedin", lambda: 0)(),
                    "checked_out": getattr(sync_pool, "checkedout", lambda: 0)(),
                    "overflow": getattr(sync_pool, "overflow", lambda: 0)(),
                },
            }

            # Try to get async pool metrics if available
            try:
                async_pool = engine.pool
                health_status["database_pools"]["async"] = {
                    "size": getattr(async_pool, "size", lambda: 0)(),
                    "checked_in": getattr(async_pool, "checkedin", lambda: 0)(),
                    "checked_out": getattr(async_pool, "checkedout", lambda: 0)(),
                    "overflow": getattr(async_pool, "overflow", lambda: 0)(),
                }
            except Exception:
                # Async pool might not be available in all contexts
                pass

        except Exception as e:
            logger.debug("Could not retrieve pool metrics", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database pool metrics unavailable",
            ) from None

    except Exception as e:
        health_status["checks"]["database"] = "unhealthy"
        health_status["status"] = "degraded"
        logger.exception("Database health check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database health check failed",
        ) from None

    return health_status


@router.get("/health/simple")
async def simple_health_check() -> dict[str, Any]:
    """
    Simple health check endpoint for load balancers.

    Returns:
        dict: Simple health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db_sync)) -> dict[str, Any]:
    """
    Detailed health check with database connectivity test.

    Returns:
        dict: Comprehensive health status including database connectivity
    """
    health_status: dict[str, Any] = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": {
            "database": {"status": "unknown", "response_time": None},
            "redis": {"status": "unknown", "response_time": None},
            "external_services": {"status": "unknown"},
        },
    }

    # Database connectivity check
    try:
        start_time = time.time()
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        db_response_time = time.time() - start_time

        health_status["checks"]["database"] = {
            "status": "healthy",
            "response_time": round(db_response_time, 3),
        }
        logger.debug("Database health check passed", response_time=db_response_time)

    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        health_status["status"] = "degraded"
        logger.exception("Database health check failed", error=str(e))

    # Redis connectivity check (if enabled)
    if settings.ENABLE_REDIS:
        try:
            from app.services.redis import get_redis_client

            start_time = time.time()
            redis_client = get_redis_client()
            if redis_client:
                await redis_client.ping()
            redis_response_time = time.time() - start_time

            health_status["checks"]["redis"] = {
                "status": "healthy",
                "response_time": round(redis_response_time, 3),
            }
            logger.debug("Redis health check passed", response_time=redis_response_time)

        except Exception as e:
            health_status["checks"]["redis"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            health_status["status"] = "degraded"
            logger.exception("Redis health check failed", error=str(e))
    else:
        health_status["checks"]["redis"] = {
            "status": "disabled",
            "message": "Redis is not enabled",
        }

    # External services check (example: email service)
    try:
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            health_status["checks"]["external_services"]["email"] = {
                "status": "configured",
                "host": settings.SMTP_HOST,
                "port": settings.SMTP_PORT,
            }
        else:
            health_status["checks"]["external_services"]["email"] = {
                "status": "not_configured",
                "message": "SMTP credentials not set",
            }
    except Exception as e:
        health_status["checks"]["external_services"]["email"] = {
            "status": "error",
            "error": str(e),
        }

    # Overall status determination
    if health_status["status"] == "degraded":
        logger.warning(
            "Health check indicates degraded service", health_status=health_status,
        )

    return health_status


@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db_sync)) -> dict[str, Any]:
    """
    Readiness check for Kubernetes/container orchestration.

    This endpoint is used by load balancers and container orchestrators
    to determine if the application is ready to receive traffic.

    Returns:
        dict: Readiness status
    """
    try:
        # Test database connectivity
        result = db.execute(text("SELECT 1"))
        result.fetchone()

        # Test Redis if enabled
        if settings.ENABLE_REDIS:
            from app.services.redis import get_redis_client

            redis_client = get_redis_client()
            if redis_client:
                await redis_client.ping()

        return {
            "ready": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {
                "database": {"ready": True},
                "application": {"ready": True},
            },
        }

    except Exception as e:
        logger.exception("Readiness check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready",
        ) from e


@router.get("/health/live")
async def liveness_check() -> dict[str, Any]:
    """
    Liveness check for Kubernetes/container orchestration.

    This endpoint is used to determine if the application is alive
    and should not be restarted.

    Returns:
        dict: Liveness status
    """
    return {
        "alive": "true",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/database")
async def database_health_check(db: Session = Depends(get_db_sync)) -> dict[str, Any]:
    """
    Detailed database health check with performance metrics.

    Returns:
        dict: Database health and performance information
    """
    try:
        start_time = time.time()

        # Test basic connectivity
        result = db.execute(text("SELECT 1"))
        result.fetchone()

        # Test more complex query
        result = db.execute(text("SELECT COUNT(*) FROM information_schema.tables"))
        row = result.fetchone()
        table_count = row[0] if row else 0

        response_time = time.time() - start_time

        # Analyze database performance
        # analyzer = QueryAnalyzer(db)  # Unused for now

        return {
            "status": "healthy",
            "response_time": round(response_time, 3),
            "table_count": table_count,
            "connection_pool": {
                "pool_size": settings.DB_POOL_SIZE,
                "max_overflow": settings.DB_MAX_OVERFLOW,
                "pool_recycle": settings.DB_POOL_RECYCLE,
            },
            "database_url": settings.DATABASE_URL.split("@")[-1],  # Hide credentials
        }

    except Exception as e:
        logger.exception("Database health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "response_time": None,
        }


@router.get("/health/rate-limit")
async def rate_limit_info() -> dict[str, Any]:
    """
    Rate limiting information endpoint.

    Returns:
        dict: Rate limiting configuration and status
    """
    return {
        "enabled": settings.ENABLE_RATE_LIMITING,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "configuration": {
            "default_limit": settings.RATE_LIMIT_DEFAULT,
            "login_limit": settings.RATE_LIMIT_LOGIN,
            "register_limit": settings.RATE_LIMIT_REGISTER,
            "storage_backend": settings.RATE_LIMIT_STORAGE_BACKEND,
        },
    }


@router.get("/health/test-sentry")
async def test_sentry_endpoint() -> dict[str, Any]:
    """
    Test endpoint for Sentry error monitoring.

    Returns:
        dict: Test error response
    """
    # Intentionally raise an exception to test Sentry
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="This is a test exception for Sentry monitoring",
    )


@router.get("/health/metrics")
async def metrics_endpoint() -> dict[str, Any]:
    """
    Application metrics endpoint for monitoring.

    Returns:
        dict: Application metrics and performance data
    """
    import psutil

    # System metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available": memory.available,
            "disk_percent": disk.percent,
            "disk_free": disk.free,
        },
        "application": {
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "features": {
                "redis_enabled": settings.ENABLE_REDIS,
                "websockets_enabled": settings.ENABLE_WEBSOCKETS,
                "celery_enabled": settings.ENABLE_CELERY,
                "rate_limiting_enabled": settings.ENABLE_RATE_LIMITING,
                "sentry_enabled": settings.ENABLE_SENTRY,
            },
        },
        "timestamp": time.time(),
    }
