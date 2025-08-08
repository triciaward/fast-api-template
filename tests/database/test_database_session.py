import asyncio

import pytest

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_get_db_closes_session(monkeypatch):
    from app.database import database as db

    closed = {"done": False}

    class FakeSession:
        async def close(self):  # type: ignore[no-untyped-def]
            closed["done"] = True

    class FakeMaker:
        def __init__(self):
            self._sess = FakeSession()

        async def __aenter__(self):  # type: ignore[no-untyped-def]
            return self._sess

        async def __aexit__(self, exc_type, exc, tb):  # type: ignore[no-untyped-def]
            return False

    fake_maker = FakeMaker()
    monkeypatch.setattr(db, "AsyncSessionLocal", lambda: fake_maker)

    agen = db.get_db()
    session = await agen.__anext__()
    assert isinstance(session, FakeSession)
    # close via aclose triggers finally block
    await agen.aclose()
    # give loop a chance to settle
    await asyncio.sleep(0)
    assert closed["done"] is True


