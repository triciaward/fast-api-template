import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel
from starlette.responses import HTMLResponse

from app.api import api_router

# Import API router dynamically based on settings
from app.bootstrap_superuser import bootstrap_superuser
from app.core import (
    configure_cors,
    configure_security_headers,
    get_app_logger,
    register_error_handlers,
    setup_logging,
)
from app.core.config import settings
from app.database.database import engine
from app.models import Base
from app.services import init_sentry

if settings.ENABLE_CELERY:
    # Import celery tasks to register them with the worker
    # Use a different approach to avoid naming conflicts
    import importlib

    importlib.import_module("app.services.background.celery_tasks")

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
        from app.services import init_redis

        logger.info("Initializing Redis connection")
        await init_redis()

    # Initialize rate limiting if enabled
    if settings.ENABLE_RATE_LIMITING:
        from app.services import init_rate_limiter

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
        from app.services import close_redis

        await close_redis()
        logger.info("Redis connection closed")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=None,
    redoc_url=None,
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
    from app.services import setup_rate_limiting

    setup_rate_limiting(app)

# Register error handlers for standardized error responses

register_error_handlers(app)

# Include API router with clean domain organization
app.include_router(api_router)


class MessageResponse(BaseModel):
    message: str


@app.get("/", response_model=MessageResponse)
async def read_root() -> MessageResponse:
    return MessageResponse(message="Welcome to FastAPI Template")


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


# Custom Swagger UI with CDN fallbacks and CSP-friendly setup
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui() -> HTMLResponse:
    """Serve Swagger UI with robust CDN fallbacks.

    This avoids upstream template issues and works with our CSP by allowing
    specific CDNs for scripts and styles.
    """
    openapi_url = f"{settings.API_V1_STR}/openapi.json"
    # Pin to a known-good Swagger UI version for stability
    swagger_version = "5.11.0"

    html = f"""
<!DOCTYPE html>
<html lang=\"en\">
  <head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>{settings.PROJECT_NAME} — API Docs</title>

    <!-- Primary CSS with non-blocking fallback -->
    <link rel=\"stylesheet\" href=\"https://unpkg.com/swagger-ui-dist@{swagger_version}/swagger-ui.css\" />
    <link rel=\"stylesheet\" href=\"https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/{swagger_version}/swagger-ui.min.css\" media=\"print\" onload=\"this.media='all'\" />

    <style>
      html {{ box-sizing: border-box; overflow-y: scroll; }}
      *, *:before, *:after {{ box-sizing: inherit; }}
      body {{ margin: 0; background: #fafafa; }}
    </style>
  </head>
  <body>
    <div id=\"swagger-ui\"></div>
    <script>
      (function() {{
        function loadScript(src, onload, onerror) {{
          var s = document.createElement('script');
          s.src = src;
          s.async = true;
          s.onload = onload;
          s.onerror = onerror || function(){{}};
          document.head.appendChild(s);
        }}

        function initUI() {{
          if (!window.SwaggerUIBundle || !window.SwaggerUIStandalonePreset) {{
            console.error('Swagger UI assets missing');
            var c = document.getElementById('swagger-ui');
            c.innerHTML = '<p style="padding:16px;color:#b00">Failed to load Swagger UI assets.</p>';
            return;
          }}
          window.ui = SwaggerUIBundle({{
            url: '{openapi_url}',
            dom_id: '#swagger-ui',
            deepLinking: true,
            presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
            layout: 'StandaloneLayout'
          }});
        }}

        // Try unpkg first, then fall back to cdnjs
        loadScript(
          'https://unpkg.com/swagger-ui-dist@{swagger_version}/swagger-ui-bundle.js',
          function() {{
            loadScript(
              'https://unpkg.com/swagger-ui-dist@{swagger_version}/swagger-ui-standalone-preset.js',
              initUI,
              function() {{
                loadScript(
                  'https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/{swagger_version}/swagger-ui-standalone-preset.min.js',
                  initUI,
                  function() {{ initUI(); }}
                );
              }}
            );
          }},
          function() {{
            loadScript(
              'https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/{swagger_version}/swagger-ui-bundle.min.js',
              function() {{
                loadScript(
                  'https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/{swagger_version}/swagger-ui-standalone-preset.min.js',
                  initUI,
                  function() {{ initUI(); }}
                );
              }},
              function() {{ initUI(); }}
            );
          }}
        );
      }})();
    </script>
  </body>
</html>
    """
    return HTMLResponse(content=html)
