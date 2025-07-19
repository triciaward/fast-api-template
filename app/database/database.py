import os
from collections.abc import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings

# Convert DATABASE_URL to async format if needed
async_database_url = settings.DATABASE_URL.replace(
    "postgresql://", "postgresql+asyncpg://")

# Create async engine
engine = create_async_engine(async_database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Create sync engine for testing
# Use test database URL if TESTING environment variable is set
if os.getenv("TESTING") == "1":
    sync_database_url = settings.DATABASE_URL.replace(
        "fastapi_template", "fastapi_template_test"
    )
else:
    sync_database_url = settings.DATABASE_URL

sync_engine = create_engine(sync_database_url, echo=False)
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
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
