import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.api_v1.api import api_router
from app.bootstrap_superuser import bootstrap_superuser
from app.core.config import settings
from app.core.cors import configure_cors
from app.core.logging_config import get_app_logger, setup_logging
from app.database.database import engine, sync_engine
from app.models import models

if settings.ENABLE_CELERY:
    # Import celery tasks to register them with the worker
    # Use a different approach to avoid naming conflicts
    import importlib
    importlib.import_module("app.services.celery_tasks")

# Setup logging
setup_logging()
logger = get_app_logger()

# Create database tables only if not in testing mode
if os.getenv("TESTING") != "1":
    models.Base.metadata.create_all(bind=sync_engine)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for FastAPI app."""
    # Startup - only create tables if not in testing mode
    if os.getenv("TESTING") != "1":
        logger.info("Starting application", environment=settings.ENVIRONMENT)

        async with engine.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)

        # Bootstrap superuser if environment variables are set
        await bootstrap_superuser()

    # Initialize Redis if enabled
    if settings.ENABLE_REDIS:
        from app.services.redis import init_redis

        logger.info("Initializing Redis connection")
        await init_redis()

    # Initialize rate limiting if enabled
    if settings.ENABLE_RATE_LIMITING:
        from app.services.rate_limiter import init_rate_limiter

        logger.info("Initializing rate limiting")
        await init_rate_limiter()

    logger.info("Application startup complete")
    yield

    # Shutdown
    logger.info("Shutting down application")
    await engine.dispose()

    # Close Redis if enabled
    if settings.ENABLE_REDIS:
        from app.services.redis import close_redis

        await close_redis()
        logger.info("Redis connection closed")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
configure_cors(app)

# Setup rate limiting
if settings.ENABLE_RATE_LIMITING:
    from app.services.rate_limiter import setup_rate_limiting

    setup_rate_limiting(app)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root() -> dict[str, str]:
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to FastAPI Template"}


# Add feature status endpoint
@app.get("/features")
async def get_features() -> dict[str, bool]:
    """Get the status of optional features."""
    logger.info("Features endpoint accessed")
    return {
        "redis": settings.ENABLE_REDIS,
        "websockets": settings.ENABLE_WEBSOCKETS,
        "rate_limiting": settings.ENABLE_RATE_LIMITING,
        "celery": settings.ENABLE_CELERY,
    }
