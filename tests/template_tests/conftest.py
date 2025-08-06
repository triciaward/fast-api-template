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
    print("CI DEBUG: .env.test loaded successfully")
except ImportError:
    print("CI DEBUG: python-dotenv not available, using default test environment")
except Exception as e:
    print(f"CI DEBUG: Error loading .env.test: {e}")

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
    print("CI DEBUG: conftest.py module loaded")
    print("CI DEBUG: RUNNING_IN_CI =", RUNNING_IN_CI)


# Verify environment variables are set
print(f"ENABLE_CELERY: {os.getenv('ENABLE_CELERY')}")
print(f"CELERY_TASK_ALWAYS_EAGER: {os.getenv('CELERY_TASK_ALWAYS_EAGER')}")

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
        }
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
        }
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
    bind=sync_test_engine, expire_on_commit=False, autocommit=False, autoflush=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    if RUNNING_IN_CI:
        print("CI DEBUG: event_loop fixture started")
    loop = asyncio.get_event_loop_policy().new_event_loop()
    if RUNNING_IN_CI:
        print("CI DEBUG: event_loop created")
    yield loop
    if RUNNING_IN_CI:
        print("CI DEBUG: event_loop fixture cleanup")
    loop.close()
    if RUNNING_IN_CI:
        print("CI DEBUG: event_loop closed")


@pytest_asyncio.fixture(scope="session")
async def setup_test_db() -> AsyncGenerator[None, None]:
    """Setup test database tables once for the session."""
    if RUNNING_IN_CI:
        print("CI DEBUG: setup_test_db fixture started - SKIPPING ASYNC IN CI")
        # In CI, just create sync tables and skip async entirely
        Base.metadata.create_all(bind=sync_test_engine)
        print("CI DEBUG: Sync tables created in CI")
        yield
        Base.metadata.drop_all(bind=sync_test_engine)
        sync_test_engine.dispose()
        print("CI DEBUG: Sync tables dropped in CI")
        return

    # Normal async setup for local development
    print("CI DEBUG: setup_test_db fixture started")

    # Create tables for async engine with timeout
    print("CI DEBUG: About to create async tables")
    try:
        # Add timeout to async operations (Python 3.11+ compatible)
        if hasattr(asyncio, "timeout"):
            async with asyncio.timeout(30):  # 30 second timeout
                async with test_engine.begin() as conn:
                    print("CI DEBUG: Inside async engine.begin()")
                    await conn.run_sync(Base.metadata.create_all)
                    print("CI DEBUG: Async tables created")
        else:
            # Fallback for Python < 3.11
            async with test_engine.begin() as conn:
                print("CI DEBUG: Inside async engine.begin() (no timeout)")
                await conn.run_sync(Base.metadata.create_all)
                print("CI DEBUG: Async tables created")
    except asyncio.TimeoutError:
        print("CI DEBUG: Timeout creating async tables - falling back to sync only")
    except Exception as e:
        print(f"CI DEBUG: Error creating async tables: {e}")
        print("CI DEBUG: Falling back to sync table creation only")
        # Fall back to sync only
        pass

    # Create tables for sync engine
    print("CI DEBUG: About to create sync tables")
    Base.metadata.create_all(bind=sync_test_engine)
    print("CI DEBUG: Sync tables created")

    print("CI DEBUG: setup_test_db fixture yielding")
    yield

    print("CI DEBUG: setup_test_db fixture cleanup started")
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
    except asyncio.TimeoutError:
        print("CI DEBUG: Timeout dropping async tables")
    except Exception as e:
        print(f"CI DEBUG: Error dropping async tables: {e}")
        try:
            await test_session_engine.dispose()
        except Exception:
            pass

    # Drop tables for sync engine
    Base.metadata.drop_all(bind=sync_test_engine)
    sync_test_engine.dispose()
    print("CI DEBUG: setup_test_db fixture cleanup completed")


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
        except Exception as e:
            # If async database doesn't have tables, that's okay
            print(f"CI DEBUG: Async cleanup failed (expected if no tables): {e}")
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
        except Exception as e:
            print(f"CI DEBUG: Session cleanup failed: {e}")
        finally:
            # Always close the session
            await session.close()


@pytest.fixture(scope="session")
def setup_sync_test_db() -> Generator[None, None, None]:
    """Setup test database tables for sync operations."""
    if RUNNING_IN_CI:
        print("CI DEBUG: setup_sync_test_db fixture started")
    # Create tables for sync engine
    Base.metadata.create_all(bind=sync_test_engine)
    if RUNNING_IN_CI:
        print("CI DEBUG: setup_sync_test_db tables created")
    yield
    if RUNNING_IN_CI:
        print("CI DEBUG: setup_sync_test_db cleanup started")
    # Drop tables for sync engine
    Base.metadata.drop_all(bind=sync_test_engine)
    sync_test_engine.dispose()
    if RUNNING_IN_CI:
        print("CI DEBUG: setup_sync_test_db cleanup completed")


@pytest.fixture
def client(setup_sync_test_db: None) -> Generator[TestClient, None, None]:
    """Create a test client with synchronous database session override."""
    if RUNNING_IN_CI:
        print("CI DEBUG: client fixture started")

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
        print("CI DEBUG: client fixture dependency overrides set")

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
