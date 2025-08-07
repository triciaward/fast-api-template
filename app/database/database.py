from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# Convert DATABASE_URL to async format if needed
async_database_url = settings.DATABASE_URL.replace(
    "postgresql://",
    "postgresql+asyncpg://",
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
        },
    },
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

# Dependency to get async DB session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
