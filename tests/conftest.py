import asyncio
import os
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.api.api_v1.api import api_router
from app.core.config import settings
from app.core.cors import configure_cors
from app.database.database import Base, get_db

# Set testing environment BEFORE importing any app modules
os.environ["TESTING"] = "1"


# Test database URLs
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:dev_password_123@localhost:5432/fastapi_template_test"
SYNC_TEST_DATABASE_URL = "postgresql://postgres:dev_password_123@localhost:5432/fastapi_template_test"

# Create async engine for direct database tests
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=False,
    pool_size=5,
    max_overflow=10,
    pool_recycle=300
)

# Create sync engine for TestClient tests
sync_test_engine = create_engine(
    SYNC_TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=False,
    pool_size=1,
    max_overflow=0
)

# Create session makers
TestingAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

TestingSyncSessionLocal = sessionmaker(
    bind=sync_test_engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def setup_test_db() -> AsyncGenerator[None, None]:
    """Setup test database tables once for the session."""
    # Create tables for async engine
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create tables for sync engine
    Base.metadata.create_all(bind=sync_test_engine)

    yield

    # Drop tables for async engine
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()

    # Drop tables for sync engine
    Base.metadata.drop_all(bind=sync_test_engine)
    sync_test_engine.dispose()


@pytest_asyncio.fixture
async def db_session(setup_test_db: None) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test with proper isolation."""
    async with TestingAsyncSessionLocal() as session:
        # Clean the database before each test
        await session.execute(text("DELETE FROM users"))
        await session.commit()

        try:
            yield session
        finally:
            # Clean up after the test, handling session state
            try:
                if session.is_active:
                    await session.execute(text("DELETE FROM users"))
                    await session.commit()
            except Exception:
                # If cleanup fails, rollback and try again
                await session.rollback()
                await session.execute(text("DELETE FROM users"))
                await session.commit()


@pytest.fixture(scope="session")
def setup_sync_test_db() -> Generator[None, None, None]:
    """Setup test database tables for sync operations."""
    # Create tables for sync engine
    Base.metadata.create_all(bind=sync_test_engine)
    yield
    # Drop tables for sync engine
    Base.metadata.drop_all(bind=sync_test_engine)
    sync_test_engine.dispose()


@pytest.fixture
def client(setup_sync_test_db: None) -> Generator[TestClient, None, None]:
    """Create a test client with synchronous database session override."""

    # Create test app without lifespan to avoid conflicts
    test_app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="FastAPI Template with Authentication",
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )

    # Configure CORS
    configure_cors(test_app)

    # Include API router
    test_app.include_router(api_router, prefix=settings.API_V1_STR)

    # Add health endpoints
    @test_app.get("/")
    async def root() -> dict[str, str]:
        return {"message": "FastAPI Template is running!"}

    @test_app.get("/health")
    async def health_check() -> dict[str, str]:
        return {"status": "healthy"}

    def override_get_db_sync() -> Generator:
        """Override to use our test-specific sync session."""
        with TestingSyncSessionLocal() as session:
            try:
                yield session
            finally:
                session.close()

    # Override the database dependency with our test-specific sync version
    test_app.dependency_overrides[get_db] = override_get_db_sync

    # Clean the database before each test
    with sync_test_engine.begin() as conn:
        conn.execute(text("DELETE FROM users"))

    with TestClient(test_app) as test_client:
        yield test_client

    # Clean the database after each test
    with sync_test_engine.begin() as conn:
        conn.execute(text("DELETE FROM users"))
        conn.commit()

    test_app.dependency_overrides.clear()


@pytest.fixture
def test_user_data() -> dict[str, str]:
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123"
    }


@pytest.fixture
def test_user_data_2() -> dict[str, str]:
    """Second sample user data for testing."""
    return {
        "email": "test2@example.com",
        "username": "testuser2",
        "password": "testpassword456"
    }
