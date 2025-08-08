import types
from datetime import datetime, timedelta, timezone

import pytest

pytestmark = pytest.mark.unit


class FakeScalars:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


class FakeResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return FakeScalars(self._items)


class FakeSession:
    def __init__(self):
        self.deleted = []
        self.added = []

    async def execute(self, *a, **k):
        # Return any pre-set items or echo based on filter intent
        return FakeResult(getattr(self, "_items", []))

    async def commit(self):
        return None

    async def refresh(self, obj):
        return None

    def add(self, obj):
        self.added.append(obj)

    async def delete(self, obj):
        self.deleted.append(obj)


def _log(event_type="login", user_id="u1", success=True, ts=None, session_id="s1"):
    if ts is None:
        ts = datetime.now(timezone.utc)
    return types.SimpleNamespace(
        event_type=event_type,
        user_id=user_id,
        success=success,
        timestamp=ts,
        session_id=session_id,
        id="id",
    )


@pytest.mark.asyncio
async def test_create_audit_log_and_refresh_tolerant(monkeypatch):
    from app.crud.system import audit_log as mod

    db = FakeSession()

    # refresh raises should be tolerated
    async def bad_refresh(obj):
        raise RuntimeError("refresh fail")

    monkeypatch.setattr(db, "refresh", bad_refresh)

    log = await mod.create_audit_log(db, "login", user_id="u1", success=True, context={"k": "v"})
    assert db.added and log.event_type == "login"


@pytest.mark.asyncio
async def test_get_audit_logs_query_helpers(monkeypatch):
    from app.crud.system import audit_log as mod

    # Prepare fake data
    now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    items = [
        _log(event_type="login", user_id="u1", success=True, ts=now, session_id="s1"),
        _log(event_type="logout", user_id=None, success=False, ts=now - timedelta(days=1), session_id="s2"),
    ]

    db = FakeSession()
    db._items = items

    # by user normal
    res = await mod.get_audit_logs_by_user(db, user_id="u1", limit=10, offset=0)
    assert len(res) == 2  # Fake returns preset regardless of filter in this stub

    # by user anonymous branch (user_id == "")
    res2 = await mod.get_audit_logs_by_user(db, user_id="", limit=10, offset=0)
    assert len(res2) == 2

    # by event type
    res3 = await mod.get_audit_logs_by_event_type(db, "login")
    assert len(res3) == 2

    # by session
    res4 = await mod.get_audit_logs_by_session(db, "s1")
    assert len(res4) == 2

    # recent
    res5 = await mod.get_recent_audit_logs(db, limit=5)
    assert len(res5) == 2

    # failed
    res6 = await mod.get_failed_audit_logs(db, limit=5)
    assert len(res6) == 2


@pytest.mark.asyncio
async def test_cleanup_old_audit_logs(monkeypatch):
    from app.crud.system import audit_log as mod

    now = datetime(2025, 1, 10, tzinfo=timezone.utc)
    old = _log(ts=now - timedelta(days=100))
    new = _log(ts=now - timedelta(days=10))

    db = FakeSession()
    # Simulate filtered execute returning only old items
    db._items = [old]

    monkeypatch.setattr(mod, "utc_now", lambda: now)

    deleted = await mod.cleanup_old_audit_logs(db, days_to_keep=90)
    assert deleted == 1 and db.deleted == [old]
