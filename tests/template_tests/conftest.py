# Set environment variables BEFORE any other imports
import asyncio
import os
import sys
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

# Import app modules early
from app.database.database import Base, get_db
from app.main import app

# Load test environment variables FIRST
try:
    import dotenv

    dotenv.load_dotenv(".env.test", override=True)
except ImportError:
    pass
except Exception:
    pass

# Set environment variables for testing
os.environ.setdefault("TESTING", "1")
os.environ.setdefault("ENABLE_CELERY", "true")
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")

# Clear config cache to force reload with new environment variables
sys.modules.pop("app.core.config", None)
sys.modules.pop("app.main", None)
sys.modules.pop("app.api.api_v1.api", None)

# Check if running in CI environment
RUNNING_IN_CI = os.getenv("RUNNING_IN_CI", "false").lower() == "true"

if RUNNING_IN_CI:
    pass


# Verify environment variables are set

# Import app AFTER environment variables are set

# Test database URLs - use environment variables if available, otherwise fallback to defaults
TEST_DATABASE_URL = os.getenv(
    "ASYNC_DATABASE_URL",
    "postgresql+asyncpg://postgres:dev_password_123@localhost:5432/fastapi_template_test",
)
SYNC_TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:dev_password_123@localhost:5432/fastapi_template_test",
)

# Create async engine for direct database tests with proper isolation
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=False,
    pool_size=5,
    max_overflow=10,
    pool_recycle=300,
    # Ensure proper isolation
    connect_args={
        "server_settings": {
            "application_name": "fastapi_template_test",
            "jit": "off",
        },
    },
)

# Create sync engine for TestClient tests with proper isolation
sync_test_engine = create_engine(
    SYNC_TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=False,
    pool_size=5,
    max_overflow=10,
    # Ensure proper isolation
    connect_args={"application_name": "fastapi_template_test"},
)

# Create a separate async engine for session tests to avoid connection conflicts
test_session_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=False,
    pool_size=2,  # Smaller pool for session tests
    max_overflow=5,
    pool_recycle=300,
    # Ensure proper isolation with different application name
    connect_args={
        "server_settings": {
            "application_name": "fastapi_template_test_sessions",
            "jit": "off",
        },
    },
)

# Create session makers
TestingAsyncSessionLocal = async_sessionmaker(
    test_session_engine,  # Use separate engine for sessions
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

TestingSyncSessionLocal = sessionmaker(
    bind=sync_test_engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    if RUNNING_IN_CI:
        pass
    loop = asyncio.get_event_loop_policy().new_event_loop()
    if RUNNING_IN_CI:
        pass
    yield loop
    if RUNNING_IN_CI:
        pass
    loop.close()
    if RUNNING_IN_CI:
        pass


@pytest_asyncio.fixture(scope="session")
async def setup_test_db() -> AsyncGenerator[None, None]:
    """Setup test database tables once for the session."""
    if RUNNING_IN_CI:
        # In CI, just create sync tables and skip async entirely
        Base.metadata.create_all(bind=sync_test_engine)
        yield
        Base.metadata.drop_all(bind=sync_test_engine)
        sync_test_engine.dispose()
        return

    # Normal async setup for local development

    # Create tables for async engine with timeout
    try:
        # Add timeout to async operations (Python 3.11+ compatible)
        if hasattr(asyncio, "timeout"):
            async with asyncio.timeout(30):  # 30 second timeout
                async with test_engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
        else:
            # Fallback for Python < 3.11
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
    except TimeoutError:
        pass
    except Exception:
        pass
        # Fall back to sync only

    # Create tables for sync engine
    Base.metadata.create_all(bind=sync_test_engine)

    yield

    # Drop tables for async engine
    try:
        if hasattr(asyncio, "timeout"):
            async with asyncio.timeout(30):  # 30 second timeout
                async with test_engine.begin() as conn:
                    await conn.run_sync(Base.metadata.drop_all)
                await test_engine.dispose()
                await test_session_engine.dispose()
        else:
            # Fallback for Python < 3.11
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            await test_engine.dispose()
            await test_session_engine.dispose()
    except TimeoutError:
        pass
    except Exception:
        try:
            await test_session_engine.dispose()
        except Exception:
            pass

    # Drop tables for sync engine
    Base.metadata.drop_all(bind=sync_test_engine)
    sync_test_engine.dispose()


@pytest_asyncio.fixture
async def db_session(setup_test_db: None) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test with proper isolation."""
    # Create a new session using the dedicated session engine
    session = TestingAsyncSessionLocal()

    try:
        # Clean the database before each test
        try:
            await session.execute(text("DELETE FROM users WHERE id IS NOT NULL"))
            await session.commit()
        except Exception:
            # If async database doesn't have tables, that's okay
            await session.rollback()

        # Yield the session for the test
        yield session
    finally:
        # Clean up after the test
        try:
            # If we're in a transaction, roll it back
            if session.in_transaction():
                await session.rollback()

            # Clean up any test data in a fresh transaction
            try:
                await session.execute(text("DELETE FROM users WHERE id IS NOT NULL"))
                await session.commit()
            except Exception:
                await session.rollback()
        except Exception:
            pass
        finally:
            # Always close the session
            await session.close()


@pytest.fixture(scope="session")
def setup_sync_test_db() -> Generator[None, None, None]:
    """Setup test database tables for sync operations."""
    if RUNNING_IN_CI:
        pass
    # Create tables for sync engine
    Base.metadata.create_all(bind=sync_test_engine)
    if RUNNING_IN_CI:
        pass
    yield
    if RUNNING_IN_CI:
        pass
    # Drop tables for sync engine
    Base.metadata.drop_all(bind=sync_test_engine)
    sync_test_engine.dispose()
    if RUNNING_IN_CI:
        pass


@pytest.fixture
def client(setup_sync_test_db: None) -> Generator[TestClient, None, None]:
    """Create a test client with synchronous database session override."""
    if RUNNING_IN_CI:
        pass

    def override_get_db_sync() -> Generator:
        """Override to use our test-specific sync session."""
        with TestingSyncSessionLocal() as session:
            try:
                yield session
            finally:
                session.close()

    # Override the database dependency with our test-specific sync version
    app.dependency_overrides[get_db] = override_get_db_sync
    if RUNNING_IN_CI:
        pass

    # Clean the database before each test - more robust cleanup
    with sync_test_engine.begin() as conn:
        conn.execute(text("DELETE FROM audit_logs"))
        conn.execute(text("DELETE FROM api_keys"))
        conn.execute(text("DELETE FROM users"))
        conn.commit()

    try:
        yield TestClient(app)
    finally:
        # Clean up after the test
        with sync_test_engine.begin() as conn:
            conn.execute(text("DELETE FROM audit_logs"))
            conn.execute(text("DELETE FROM api_keys"))
            conn.execute(text("DELETE FROM users"))
            conn.commit()
        app.dependency_overrides.clear()


@pytest.fixture
def sync_db_session(setup_sync_test_db: None) -> Generator:
    """Create a synchronous database session for tests that need sync operations."""
    with TestingSyncSessionLocal() as session:
        # Clean the database before each test
        session.execute(text("DELETE FROM audit_logs"))
        session.execute(text("DELETE FROM api_keys"))
        session.execute(text("DELETE FROM users"))
        session.commit()

        try:
            yield session
        finally:
            # Clean up after the test
            try:
                session.execute(text("DELETE FROM audit_logs"))
                session.execute(text("DELETE FROM api_keys"))
                session.execute(text("DELETE FROM users"))
                session.commit()
            except Exception:
                session.rollback()
                session.execute(text("DELETE FROM audit_logs"))
                session.execute(text("DELETE FROM api_keys"))
                session.execute(text("DELETE FROM users"))
                session.commit()


@pytest.fixture
def test_user_data() -> dict[str, str]:
    """Sample user data for testing."""
    return {
        "email": "unique_test_user@example.com",
        "username": "unique_testuser",
        "password": "TestPassword123!",
    }


@pytest.fixture
def test_user_data_2() -> dict[str, str]:
    """Second sample user data for testing."""
    return {
        "email": "test2@example.com",
        "username": "testuser2",
        "password": "TestPassword456!",
    }
