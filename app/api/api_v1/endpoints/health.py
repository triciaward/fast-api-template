from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.database import engine, get_db, sync_engine
from app.services.sentry import capture_exception, capture_message, is_sentry_working


def safe_pool_stat(pool, name: str, default: int = 0) -> int:
    """Safely get pool statistics, handling missing attributes gracefully."""
    if hasattr(pool, name):
        attr = getattr(pool, name)
        if callable(attr):
            return attr()
        return attr
    return default


router = APIRouter()


def utc_now() -> datetime:
    """Get current UTC datetime (replaces deprecated utc_now())."""
    return datetime.now(timezone.utc)


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    Comprehensive health check endpoint for monitoring and container orchestration.

    Returns:
        dict: Health status including database connectivity, app status, and metadata
    """
    health_status: dict[str, Any] = {
        "status": "healthy",
        "timestamp": utc_now().isoformat(),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": {"database": "healthy", "application": "healthy"},
    }

    # Add Sentry status
    if settings.ENABLE_SENTRY:
        sentry_working = is_sentry_working()
        health_status["checks"]["sentry"] = "enabled" if sentry_working else "error"
        health_status["sentry"] = {
            "enabled": True,
            "working": sentry_working,
            "environment": settings.SENTRY_ENVIRONMENT,
            "dsn_configured": bool(settings.SENTRY_DSN),
        }
    else:
        health_status["checks"]["sentry"] = "disabled"
        health_status["sentry"] = {"enabled": False}

    # Check database connectivity and pool status
    try:
        # Execute a simple query to verify database connection
        result = await db.execute(text("SELECT 1"))
        result.fetchone()
        health_status["checks"]["database"] = "healthy"

        # Add connection pool information
        async_pool = engine.pool
        sync_pool = sync_engine.pool

        health_status["database_pools"] = {
            "async": {
                "size": safe_pool_stat(async_pool, "size"),
                "checked_in": safe_pool_stat(async_pool, "checkedin"),
                "checked_out": safe_pool_stat(async_pool, "checkedout"),
                "overflow": safe_pool_stat(async_pool, "overflow"),
            },
            "sync": {
                "size": safe_pool_stat(sync_pool, "size"),
                "checked_in": safe_pool_stat(sync_pool, "checkedin"),
                "checked_out": safe_pool_stat(sync_pool, "checkedout"),
                "overflow": safe_pool_stat(sync_pool, "overflow"),
            },
        }

        # Add 'invalid' attribute if available
        if hasattr(async_pool, "invalid"):
            health_status["database_pools"]["async"]["invalid"] = safe_pool_stat(
                async_pool, "invalid"
            )
        if hasattr(sync_pool, "invalid"):
            health_status["database_pools"]["sync"]["invalid"] = safe_pool_stat(
                sync_pool, "invalid"
            )

    except Exception as e:
        health_status["checks"]["database"] = "unhealthy"
        health_status["status"] = "unhealthy"
        health_status["database_error"] = str(e)
        # Capture database error in Sentry
        capture_exception(e, {"check": "database", "endpoint": "health"})

    # Check Redis connectivity if enabled
    if settings.ENABLE_REDIS:
        try:
            from app.services.redis import health_check_redis

            redis_healthy = await health_check_redis()
            health_status["checks"]["redis"] = (
                "healthy" if redis_healthy else "unhealthy"
            )
            if not redis_healthy:
                health_status["status"] = "unhealthy"
        except Exception as e:
            health_status["checks"]["redis"] = "unhealthy"
            health_status["status"] = "unhealthy"
            health_status["redis_error"] = str(e)

    # Check rate limiting status if enabled
    if settings.ENABLE_RATE_LIMITING:
        try:
            from app.services.rate_limiter import get_limiter

            limiter = get_limiter()
            if limiter:
                health_status["checks"]["rate_limiting"] = "healthy"
            else:
                health_status["checks"]["rate_limiting"] = "unhealthy"
                health_status["status"] = "unhealthy"
        except Exception as e:
            health_status["checks"]["rate_limiting"] = "unhealthy"
            health_status["status"] = "unhealthy"
            health_status["rate_limiting_error"] = str(e)

    # Check Celery status if enabled
    if settings.ENABLE_CELERY:
        try:
            from app.services.celery import get_celery_stats

            celery_stats = get_celery_stats()
            if celery_stats.get("enabled", False):
                health_status["checks"]["celery"] = "healthy"
                health_status["celery_stats"] = celery_stats
            else:
                health_status["checks"]["celery"] = "unhealthy"
                health_status["status"] = "unhealthy"
                if "error" in celery_stats:
                    health_status["celery_error"] = celery_stats["error"]
        except Exception as e:
            health_status["checks"]["celery"] = "unhealthy"
            health_status["status"] = "unhealthy"
            health_status["celery_error"] = str(e)

    # Determine overall status
    if health_status["checks"]["database"] == "unhealthy":
        health_status["status"] = "unhealthy"

    return health_status


@router.get("/health/simple")
async def simple_health_check() -> dict[str, str]:
    """
    Simple health check endpoint for basic uptime monitoring.

    Returns:
        dict: Basic health status
    """
    return {"status": "healthy", "timestamp": utc_now().isoformat()}


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    Readiness check endpoint for Kubernetes readiness probes.

    Returns:
        dict: Readiness status with detailed component checks
    """
    readiness_status: dict[str, Any] = {
        "ready": True,
        "timestamp": utc_now().isoformat(),
        "components": {
            "database": {"ready": True, "message": "Database connection successful"},
            "application": {"ready": True, "message": "Application is running"},
        },
    }

    # Check database readiness
    try:
        result = await db.execute(text("SELECT 1"))
        result.fetchone()
        readiness_status["components"]["database"]["ready"] = True
        readiness_status["components"]["database"][
            "message"
        ] = "Database connection successful"
    except Exception as e:
        readiness_status["components"]["database"]["ready"] = False
        readiness_status["components"]["database"][
            "message"
        ] = f"Database connection failed: {str(e)}"
        readiness_status["ready"] = False

    # Check Redis readiness if enabled
    if settings.ENABLE_REDIS:
        try:
            from app.services.redis import health_check_redis

            redis_ready = await health_check_redis()
            readiness_status["components"]["redis"] = {
                "ready": redis_ready,
                "message": (
                    "Redis connection successful"
                    if redis_ready
                    else "Redis connection failed"
                ),
            }
            if not redis_ready:
                readiness_status["ready"] = False
        except Exception as e:
            readiness_status["components"]["redis"] = {
                "ready": False,
                "message": f"Redis connection failed: {str(e)}",
            }
            readiness_status["ready"] = False

    # Check rate limiting readiness if enabled
    if settings.ENABLE_RATE_LIMITING:
        try:
            from app.services.rate_limiter import get_limiter

            limiter = get_limiter()
            readiness_status["components"]["rate_limiting"] = {
                "ready": limiter is not None,
                "message": (
                    "Rate limiting ready"
                    if limiter
                    else "Rate limiting not initialized"
                ),
            }
            if not limiter:
                readiness_status["ready"] = False
        except Exception as e:
            readiness_status["components"]["rate_limiting"] = {
                "ready": False,
                "message": f"Rate limiting failed: {str(e)}",
            }
            readiness_status["ready"] = False

    # Check Celery readiness if enabled
    if settings.ENABLE_CELERY:
        try:
            from app.services.celery import get_celery_stats

            celery_stats = get_celery_stats()
            if celery_stats.get("enabled", False):
                readiness_status["components"]["celery"] = {
                    "ready": True,
                    "message": "Celery ready",
                }
            else:
                readiness_status["components"]["celery"] = {
                    "ready": False,
                    "message": "Celery not initialized",
                }
                readiness_status["ready"] = False
        except Exception as e:
            readiness_status["components"]["celery"] = {
                "ready": False,
                "message": f"Celery failed: {str(e)}",
            }
            readiness_status["ready"] = False

    # Determine overall readiness
    if not readiness_status["ready"]:
        raise HTTPException(
            status_code=503,
            detail={
                "ready": False,
                "message": "Service not ready",
                "components": readiness_status["components"],
            },
        )

    return readiness_status


@router.get("/health/live")
async def liveness_check() -> dict[str, str]:
    """
    Liveness check endpoint for Kubernetes liveness probes.

    Returns:
        dict: Liveness status
    """
    return {"alive": "true", "timestamp": utc_now().isoformat()}


@router.get("/health/rate-limit")
async def rate_limit_info(request: Request) -> dict[str, Any]:
    """
    Get current rate limit information for the requesting client.

    Returns:
        dict: Rate limit information including remaining requests and reset time
    """
    if not settings.ENABLE_RATE_LIMITING:
        return {
            "enabled": False,
            "message": "Rate limiting is disabled",
        }

    try:
        from app.services.rate_limiter import get_rate_limit_info

        return get_rate_limit_info(request)
    except Exception as e:
        return {
            "enabled": True,
            "error": str(e),
            "message": "Failed to get rate limit information",
        }


@router.get("/health/test-sentry")
async def test_sentry_monitoring() -> dict[str, str]:
    """
    Test endpoint to demonstrate Sentry error monitoring.

    This endpoint intentionally raises an exception to test error capture.
    """
    try:
        # Capture a test message
        capture_message(
            "Testing Sentry message capture", "info", {"test": "health_endpoint"}
        )

        # Intentionally raise an exception to test error capture
        raise ValueError("This is a test exception for Sentry monitoring")

    except Exception as e:
        # Capture the exception with context
        capture_exception(
            e,
            {
                "test": "sentry_monitoring",
                "endpoint": "health/test-sentry",
                "intentional": True,
            },
        )

        # Re-raise to return proper HTTP error
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Test exception captured by Sentry",
                "message": str(e),
                "test": True,
            },
        ) from e
