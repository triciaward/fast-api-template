# Set environment variables BEFORE any other imports
import asyncio
import os
import subprocess
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
from app.models.user import User  # Import User for type annotations

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
    pool_size=1,  # Use single connection to avoid conflicts
    max_overflow=0,  # No overflow connections
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


@pytest_asyncio.fixture(scope="function")
async def setup_async_test_db() -> AsyncGenerator[None, None]:
    """Setup test database tables for async tests using existing sync migration setup."""
    if RUNNING_IN_CI:
        # In CI, skip async database setup
        yield
        return

    # The sync setup already ran migrations, so async tests can use the same database
    # Just verify tables exist
    try:
        # Test if tables exist by trying a simple query
        if hasattr(asyncio, "timeout"):
            async with asyncio.timeout(30):  # 30 second timeout
                async with test_engine.begin() as conn:
                    # Test if audit_logs table exists
                    await conn.execute(
                        text(
                            "SELECT 1 FROM information_schema.tables WHERE table_name='audit_logs'",
                        ),
                    )
        else:
            # Fallback for Python < 3.11
            async with test_engine.begin() as conn:
                await conn.execute(
                    text(
                        "SELECT 1 FROM information_schema.tables WHERE table_name='audit_logs'",
                    ),
                )
    except TimeoutError:
        pass
    except Exception:
        # If tables don't exist, create them
        try:
            if hasattr(asyncio, "timeout"):
                async with asyncio.timeout(30):
                    async with test_engine.begin() as conn:
                        await conn.run_sync(Base.metadata.create_all)
            else:
                async with test_engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
        except Exception:
            pass

    yield

    # Don't drop tables here since sync tests might still need them
    # Cleanup is handled by the sync fixture
    try:
        await test_engine.dispose()
        await test_session_engine.dispose()
    except Exception:
        try:
            await test_session_engine.dispose()
        except Exception:
            pass


@pytest_asyncio.fixture
async def db_session(setup_async_test_db: None) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test with proper isolation."""
    # Create a new session using the dedicated session engine
    session = TestingAsyncSessionLocal()

    try:
        # Clean the database before each test
        try:
            # Use CASCADE delete to handle foreign key constraints
            await session.execute(text("DELETE FROM audit_logs"))
            await session.execute(text("DELETE FROM api_keys"))
            await session.execute(text("DELETE FROM refresh_tokens"))
            await session.execute(text("DELETE FROM users"))
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
                # Use CASCADE delete to handle foreign key constraints
                await session.execute(text("DELETE FROM audit_logs"))
                await session.execute(text("DELETE FROM api_keys"))
                await session.execute(text("DELETE FROM refresh_tokens"))
                await session.execute(text("DELETE FROM users"))
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
    """Setup test database tables for sync operations using Alembic migrations."""
    if RUNNING_IN_CI:
        pass

    # Run Alembic migrations to create all tables (including audit_logs)
    try:
        # Set environment variables for test database
        test_env = os.environ.copy()
        test_env["DATABASE_URL"] = SYNC_TEST_DATABASE_URL
        test_env["ASYNC_DATABASE_URL"] = TEST_DATABASE_URL
        test_env["TESTING"] = "1"

        # Run migrations
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            env=test_env,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            # Fallback to create_all if migrations fail
            Base.metadata.create_all(bind=sync_test_engine)
    except Exception:
        # Fallback to create_all if migrations fail
        Base.metadata.create_all(bind=sync_test_engine)

    if RUNNING_IN_CI:
        pass
    yield
    if RUNNING_IN_CI:
        pass

    # Clean up: Drop all tables
    try:
        # Use Alembic to downgrade
        test_env = os.environ.copy()
        test_env["DATABASE_URL"] = SYNC_TEST_DATABASE_URL
        test_env["ASYNC_DATABASE_URL"] = TEST_DATABASE_URL
        test_env["TESTING"] = "1"

        subprocess.run(
            ["alembic", "downgrade", "base"],
            env=test_env,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except Exception:
        # Fallback to drop_all
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
        try:
            conn.execute(text("DELETE FROM users"))
            conn.commit()
        except Exception:
            conn.rollback()

    try:
        yield TestClient(app)
    finally:
        # Clean up after the test
        with sync_test_engine.begin() as conn:
            try:
                conn.execute(text("DELETE FROM users"))
                conn.commit()
            except Exception:
                conn.rollback()
        app.dependency_overrides.clear()


@pytest.fixture
def sync_db_session(setup_sync_test_db: None) -> Generator:
    """Create a synchronous database session for tests that need sync operations."""
    with TestingSyncSessionLocal() as session:
        # Clean the database before each test
        try:
            session.execute(text("DELETE FROM users"))
            session.commit()
        except Exception:
            session.rollback()

        try:
            yield session
        finally:
            # Clean up after the test
            try:
                if session.in_transaction():
                    session.rollback()

                # Clean up test data
                try:
                    session.execute(text("DELETE FROM users"))
                    session.commit()
                except Exception:
                    session.rollback()
            except Exception:
                pass


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


@pytest.fixture
def test_user(sync_db_session) -> User:
    """Create a test user for sync tests."""
    from app.core.security import get_password_hash

    # Create a test user
    hashed_password = get_password_hash("TestPassword123!")
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=hashed_password,
        is_active=True,
        is_verified=True,
    )
    sync_db_session.add(user)
    sync_db_session.commit()
    sync_db_session.refresh(user)
    return user


@pytest.fixture
def test_user_token(test_user) -> str:
    """Create a test user token for authentication tests."""
    from datetime import timedelta

    from app.core.security import create_access_token

    access_token_expires = timedelta(minutes=60)
    return create_access_token(
        subject=test_user.id,
        expires_delta=access_token_expires,
    )


@pytest_asyncio.fixture
async def isolated_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create an isolated async database session that doesn't interfere with other tests.

    This fixture is for tests that need async database access but might conflict
    with other async tests when run concurrently.
    """
    # Create a completely separate engine for isolated tests
    isolated_engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=False,
        pool_size=1,  # Single connection only
        max_overflow=0,  # No overflow
        pool_recycle=300,
        connect_args={
            "server_settings": {
                "application_name": "fastapi_template_test_isolated",
                "jit": "off",
            },
        },
    )

    # Create session maker for this isolated engine
    IsolatedSessionLocal = async_sessionmaker(
        isolated_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    session = IsolatedSessionLocal()

    try:
        # Clean the database before the test
        try:
            await session.execute(text("DELETE FROM audit_logs"))
            await session.execute(text("DELETE FROM api_keys"))
            await session.execute(text("DELETE FROM refresh_tokens"))
            await session.execute(text("DELETE FROM users"))
            await session.commit()
        except Exception:
            await session.rollback()

        yield session

    finally:
        # Clean up after the test
        try:
            if session.in_transaction():
                await session.rollback()

            # Clean up test data
            try:
                await session.execute(text("DELETE FROM audit_logs"))
                await session.execute(text("DELETE FROM api_keys"))
                await session.execute(text("DELETE FROM refresh_tokens"))
                await session.execute(text("DELETE FROM users"))
                await session.commit()
            except Exception:
                await session.rollback()
        except Exception:
            pass
        finally:
            await session.close()
            await isolated_engine.dispose()
