from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.database import get_db

router = APIRouter()


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    Comprehensive health check endpoint for monitoring and container orchestration.

    Returns:
        dict: Health status including database connectivity, app status, and metadata
    """
    health_status: dict[str, Any] = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": {"database": "healthy", "application": "healthy"},
    }

    # Check database connectivity
    try:
        # Execute a simple query to verify database connection
        result = await db.execute(text("SELECT 1"))
        result.fetchone()
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = "unhealthy"
        health_status["status"] = "unhealthy"
        health_status["database_error"] = str(e)

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
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    Readiness check endpoint for Kubernetes readiness probes.

    Returns:
        dict: Readiness status with detailed component checks
    """
    readiness_status: dict[str, Any] = {
        "ready": True,
        "timestamp": datetime.utcnow().isoformat(),
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
    return {"alive": "true", "timestamp": datetime.utcnow().isoformat()}
