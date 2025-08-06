import os
from collections.abc import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings

# Convert DATABASE_URL to async format if needed
async_database_url = settings.DATABASE_URL.replace(
    "postgresql://", "postgresql+asyncpg://"
)

# Create async engine with connection pooling
engine = create_async_engine(
    async_database_url,
    echo=False,
    # Connection pooling settings
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=settings.DB_POOL_PRE_PING,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    # Connection settings
    connect_args={
        "server_settings": {
            "application_name": "fastapi_template",
            "jit": "off",  # Disable JIT for better performance
        }
    },
)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Create sync engine for testing
# Use test database URL if TESTING environment variable is set
if os.getenv("TESTING") == "1":
    # Check if the URL already contains the test database name
    if "fastapi_template_test" in settings.DATABASE_URL:
        sync_database_url = settings.DATABASE_URL
    else:
        sync_database_url = settings.DATABASE_URL.replace(
            "fastapi_template", "fastapi_template_test"
        )
else:
    sync_database_url = settings.DATABASE_URL

sync_engine = create_engine(
    sync_database_url,
    echo=False,
    # Connection pooling settings for sync engine
    # Smaller pool for sync operations
    pool_size=min(settings.DB_POOL_SIZE, 10),
    max_overflow=min(settings.DB_MAX_OVERFLOW, 20),
    pool_pre_ping=settings.DB_POOL_PRE_PING,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    # Connection settings
    connect_args={
        "application_name": (
            "fastapi_template_test"
            if os.getenv("TESTING") == "1"
            else "fastapi_template"
        )
    },
)
SyncSessionLocal = sessionmaker(
    bind=sync_engine, expire_on_commit=False, autocommit=False, autoflush=False
)

Base = declarative_base()

# Dependency to get async DB session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Dependency to get sync DB session for testing
def get_db_sync() -> Generator[Session, None, None]:
    with SyncSessionLocal() as session:
        try:
            yield session
        finally:
            session.close()
