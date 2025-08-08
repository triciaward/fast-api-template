import types

import pytest

pytestmark = pytest.mark.unit


class DummyResult:
    def __init__(self, value=None):
        self._value = value or []

    def scalars(self):
        return types.SimpleNamespace(all=lambda: self._value)


class DummySession:
    def __init__(self):
        self.added = []
        self.deleted = []

    async def execute(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        return DummyResult([])

    def add(self, obj):  # type: ignore[no-untyped-def]
        self.added.append(obj)

    async def commit(self):
        return None

    async def refresh(self, *args, **kwargs):
        return None

    async def delete(self, obj):
        self.deleted.append(obj)


@pytest.mark.asyncio
async def test_create_audit_log_smoke():
    from app.crud.system.audit_log import create_audit_log

    db = DummySession()
    log = await create_audit_log(db, event_type="login_success", user_id=None, success=True)
    assert db.added and log is not None


@pytest.mark.asyncio
async def test_list_recent_and_failed_smoke():
    from app.crud.system import audit_log as crud

    db = DummySession()
    # These should return lists with our DummyResult ([])
    recent = await crud.get_recent_audit_logs(db)
    failed = await crud.get_failed_audit_logs(db)
    assert isinstance(recent, list) and isinstance(failed, list)
