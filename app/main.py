import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.admin_router import router as admin_html_router
from app.api.api_v1.api import create_api_router

# Import API router dynamically based on settings
from app.bootstrap_superuser import bootstrap_superuser
from app.core.config import settings
from app.core.cors import configure_cors
from app.core.error_handlers import register_error_handlers
from app.core.logging_config import get_app_logger, setup_logging
from app.core.security_headers import configure_security_headers
from app.database.database import engine
from app.models import Base
from app.services.sentry import init_sentry

if settings.ENABLE_CELERY:
    # Import celery tasks to register them with the worker
    # Use a different approach to avoid naming conflicts
    import importlib

    importlib.import_module("app.services.celery_tasks")

# Setup logging
setup_logging()
logger = get_app_logger()

# Production environment validation
if settings.ENVIRONMENT == "production":
    if settings.SECRET_KEY == "dev_secret_key_change_in_production":
        logger.warning(
            "⚠️  CRITICAL SECURITY WARNING: Using default secret key in production! "
            "Please set a secure SECRET_KEY environment variable.",
        )
    if not settings.REFRESH_TOKEN_COOKIE_SECURE:
        logger.warning(
            "⚠️  SECURITY WARNING: REFRESH_TOKEN_COOKIE_SECURE is False in production. "
            "Set to True for HTTPS environments.",
        )
    if not settings.ENABLE_HSTS:
        logger.warning(
            "⚠️  SECURITY WARNING: HSTS is disabled in production. "
            "Enable ENABLE_HSTS=True for HTTPS environments.",
        )

# Database tables will be created in the lifespan context manager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for FastAPI app."""
    # Startup - only create tables if not in testing mode
    if os.getenv("TESTING") != "1":
        logger.info("Starting application", environment=settings.ENVIRONMENT)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

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

    # Initialize Sentry error monitoring
    init_sentry()

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

# Configure Security Headers
if settings.ENABLE_SECURITY_HEADERS:
    configure_security_headers(app)

# Setup Sentry ASGI middleware for better request context
if settings.ENABLE_SENTRY:
    from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

    app.add_middleware(SentryAsgiMiddleware)

# Setup rate limiting
if settings.ENABLE_RATE_LIMITING:
    from app.services.rate_limiter import setup_rate_limiting

    setup_rate_limiting(app)

# Register error handlers for standardized error responses

register_error_handlers(app)

# Include API router dynamically based on settings
app.include_router(create_api_router(), prefix=settings.API_V1_STR)

# Include admin HTML router
app.include_router(admin_html_router, prefix="/admin", tags=["admin-html"])


@app.get("/")
async def root() -> dict[str, str]:
    """
    Root endpoint for the FastAPI application.

    Returns:
        dict: Welcome message with application information
    """
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to FastAPI Template"}


# Add feature status endpoint
@app.get("/features")
async def get_features() -> dict[str, bool]:
    """
    Get the status of optional features.

    Returns:
        dict: Dictionary mapping feature names to their enabled status
    """
    logger.info("Features endpoint accessed")
    return {
        "redis": settings.ENABLE_REDIS,
        "websockets": settings.ENABLE_WEBSOCKETS,
        "rate_limiting": settings.ENABLE_RATE_LIMITING,
        "celery": settings.ENABLE_CELERY,
    }
