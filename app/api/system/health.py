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
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.users.auth import require_api_scope
from app.core.config import settings
from app.core.config.logging_config import get_app_logger
from app.database.database import get_db
from app.schemas.auth.user import APIKeyUser

router = APIRouter()
logger = get_app_logger()


class HealthStatus(BaseModel):
    status: str
    timestamp: str
    version: str
    environment: str
    checks: dict[str, Any]
    sentry: dict[str, Any] | None = None


class SimpleHealthResponse(BaseModel):
    status: str
    timestamp: str


class DetailedHealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    environment: str
    checks: dict[str, Any]


class ReadinessResponse(BaseModel):
    ready: bool
    timestamp: str
    components: dict[str, Any]


class LivenessResponse(BaseModel):
    alive: str
    timestamp: str


class DatabaseHealthResponse(BaseModel):
    status: str
    response_time: float | None = Field(default=None)
    table_count: int | None = Field(default=None)
    connection_pool: dict[str, Any] | None = Field(default=None)
    database_url: str | None = Field(default=None)
    error: str | None = Field(default=None)


class RateLimitInfoResponse(BaseModel):
    enabled: bool
    timestamp: str
    configuration: dict[str, Any]


class MetricsResponse(BaseModel):
    system: dict[str, Any]
    application: dict[str, Any]
    timestamp: float


@router.get("/health", response_model=dict)
async def health_check(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
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
        result = await db.execute(text("SELECT 1"))
        result.fetchone()  # fetchone() doesn't need to be awaited
        health_status["checks"]["database"] = "healthy"
        logger.debug("Database health check passed")

        # Add database pool metrics if database is healthy
        try:
            from app.database.database import engine

            # Get async pool metrics
            async_pool = engine.pool
            health_status["database_pools"] = {
                "async": {
                    "size": getattr(async_pool, "size", lambda: 0)(),
                    "checked_in": getattr(async_pool, "checkedin", lambda: 0)(),
                    "checked_out": getattr(async_pool, "checkedout", lambda: 0)(),
                    "overflow": getattr(async_pool, "overflow", lambda: 0)(),
                },
            }

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


@router.get("/health/simple", response_model=SimpleHealthResponse)
async def simple_health_check() -> SimpleHealthResponse:
    """
    Simple health check endpoint for load balancers.

    Returns:
        dict: Simple health status
    """
    return SimpleHealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check(
    db: AsyncSession = Depends(get_db),
    _: APIKeyUser = Depends(require_api_scope("system:read")),
) -> DetailedHealthResponse:
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
        result = await db.execute(text("SELECT 1"))
        result.fetchone()  # fetchone() doesn't need to be awaited
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
            from app.services.external.redis import get_redis_client

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
            "Health check indicates degraded service",
            health_status=health_status,
        )

    return DetailedHealthResponse.model_validate(health_status)


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness_check(db: AsyncSession = Depends(get_db)) -> ReadinessResponse:
    """
    Readiness check for Kubernetes/container orchestration.

    This endpoint is used by load balancers and container orchestrators
    to determine if the application is ready to receive traffic.

    Returns:
        dict: Readiness status
    """
    try:
        # Test database connectivity
        result = await db.execute(text("SELECT 1"))
        result.fetchone()  # fetchone() doesn't need to be awaited

        # Test Redis if enabled
        if settings.ENABLE_REDIS:
            from app.services.external.redis import get_redis_client

            redis_client = get_redis_client()
            if redis_client:
                await redis_client.ping()

        return ReadinessResponse(
            ready=True,
            timestamp=datetime.now(timezone.utc).isoformat(),
            components={
                "database": {"ready": True},
                "application": {"ready": True},
            },
        )

    except Exception as e:
        logger.exception("Readiness check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready",
        ) from e


@router.get("/health/live", response_model=LivenessResponse)
async def liveness_check() -> LivenessResponse:
    """
    Liveness check for Kubernetes/container orchestration.

    This endpoint is used to determine if the application is alive
    and should not be restarted.

    Returns:
        dict: Liveness status
    """
    return LivenessResponse(
        alive="true",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/health/database", response_model=DatabaseHealthResponse)
async def database_health_check(
    db: AsyncSession = Depends(get_db),
    _: APIKeyUser = Depends(require_api_scope("system:read")),
) -> DatabaseHealthResponse:
    """
    Detailed database health check with performance metrics.

    Returns:
        dict: Database health and performance information
    """
    try:
        start_time = time.time()

        # Test basic connectivity
        result = await db.execute(text("SELECT 1"))
        result.fetchone()  # fetchone() doesn't need to be awaited

        # Test more complex query
        result = await db.execute(
            text("SELECT COUNT(*) FROM information_schema.tables"),
        )
        row = result.fetchone()  # fetchone() doesn't need to be awaited
        table_count = row[0] if row else 0

        response_time = time.time() - start_time

        # Analyze database performance
        # analyzer = QueryAnalyzer(db)  # Unused for now

        return DatabaseHealthResponse(
            status="healthy",
            response_time=round(response_time, 3),
            table_count=table_count,
            connection_pool={
                "pool_size": settings.DB_POOL_SIZE,
                "max_overflow": settings.DB_MAX_OVERFLOW,
                "pool_recycle": settings.DB_POOL_RECYCLE,
            },
            database_url=settings.DATABASE_URL.split("@")[-1],
        )

    except Exception as e:
        logger.exception("Database health check failed", error=str(e))
        return DatabaseHealthResponse(
            status="unhealthy",
            error=str(e),
            response_time=None,
        )


@router.get("/health/rate-limit", response_model=RateLimitInfoResponse)
async def rate_limit_info() -> RateLimitInfoResponse:
    """
    Rate limiting information endpoint.

    Returns:
        dict: Rate limiting configuration and status
    """
    return RateLimitInfoResponse(
        enabled=settings.ENABLE_RATE_LIMITING,
        timestamp=datetime.now(timezone.utc).isoformat(),
        configuration={
            "default_limit": settings.RATE_LIMIT_DEFAULT,
            "login_limit": settings.RATE_LIMIT_LOGIN,
            "register_limit": settings.RATE_LIMIT_REGISTER,
            "storage_backend": settings.RATE_LIMIT_STORAGE_BACKEND,
        },
    )


@router.get("/health/test-sentry")
async def test_sentry_endpoint(
    _: APIKeyUser = Depends(require_api_scope("system:read")),
) -> dict[str, Any]:
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


@router.get("/health/metrics", response_model=MetricsResponse)
async def metrics_endpoint(
    _: APIKeyUser = Depends(require_api_scope("system:read")),
) -> MetricsResponse:
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

    return MetricsResponse(
        system={
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available": memory.available,
            "disk_percent": disk.percent,
            "disk_free": disk.free,
        },
        application={
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
        timestamp=time.time(),
    )
