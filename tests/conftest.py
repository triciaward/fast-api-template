import os

# Ensure app lifespan avoids external side-effects during tests
os.environ.setdefault("TESTING", "1")

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import database as db_module
from app.database.database import get_db as real_get_db
from app.main import app


# Replace real engine with a no-op engine to avoid opening sockets during tests
class _NoOpEngine:
    pool = None

    async def dispose(self) -> None:
        return None


db_module.engine = _NoOpEngine()  # type: ignore[assignment]


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    # When providing a custom transport to httpx.AsyncClient, the caller must close it.
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client  # type: ignore[misc]
    # Ensure transport is properly closed to avoid ResourceWarning: unclosed transport
    await transport.aclose()


@pytest.fixture(autouse=True)
def _override_db_dependency():
    """Prevent real DB sessions from being created; yield a dummy session.

    Tests that need DB should override explicitly per-test.
    """

    class _FakeResult:
        def scalar(self):
            return 0

        def scalar_one_or_none(self):
            return None

        def fetchone(self):
            return (1,)

    class DummySession:
        async def execute(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            return _FakeResult()

        def add(self, *args, **kwargs):
            return None

        async def commit(self) -> None:
            return None

        async def refresh(self, *args, **kwargs) -> None:
            return None

        async def close(self) -> None:
            return None

    async def fake_get_db() -> AsyncGenerator[DummySession, None]:  # type: ignore[no-untyped-def]
        yield DummySession()  # type: ignore[misc]

    app.dependency_overrides[real_get_db] = fake_get_db
    try:
        yield
    finally:
        app.dependency_overrides.pop(real_get_db, None)
