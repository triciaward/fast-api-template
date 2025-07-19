import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.api_v1.api import api_router
from app.bootstrap_superuser import bootstrap_superuser
from app.core.config import settings
from app.core.cors import configure_cors
from app.database.database import engine
from app.models import models


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for FastAPI app."""
    # Startup - only create tables if not in testing mode
    if os.getenv("TESTING") != "1":
        async with engine.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)

        # Bootstrap superuser if environment variables are set
        await bootstrap_superuser()
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="FastAPI Template with Authentication",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Configure CORS
configure_cors(app)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "FastAPI Template is running!"}
