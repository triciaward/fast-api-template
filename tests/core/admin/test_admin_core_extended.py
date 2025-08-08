import types

import pytest

pytestmark = pytest.mark.unit


class DummyResult:
    def __init__(self, value=None):
        self._value = value

    def scalars(self):
        vals = self._value if isinstance(self._value, list) else []
        return types.SimpleNamespace(all=lambda: vals)

    def scalar_one_or_none(self):
        return self._value

    def scalar(self):
        return 0 if self._value is None else self._value


class DummySession:
    async def execute(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        # Return empty results; specific tests override via monkeypatch if needed
        return DummyResult([])

    async def delete(self, obj):
        return None

    async def commit(self):
        return None


class Model:
    id = "id"
    field = "x"

    def __init__(self, id):  # noqa: A002
        self.id = id
        self.field = "x"


class FakeSelect:
    def __init__(self):
        pass

    # Chainable methods to mimic SQLAlchemy Select API
    def where(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def offset(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self


@pytest.mark.asyncio
async def test_get_multi_with_filters(monkeypatch):
    from app.core.admin import admin as admin_module

    # Patch select to our FakeSelect
    monkeypatch.setattr(admin_module, "select", lambda *a, **k: FakeSelect())

    items = [Model("1"), Model("2")]

    async def fake_execute(self, query):
        return DummyResult(items)

    monkeypatch.setattr(DummySession, "execute", fake_execute, raising=False)

    crud = admin_module.BaseAdminCRUD(Model)
    result = await crud.get_multi(
        DummySession(),
        skip=0,
        limit=10,
        filters={"field": "x"},
    )
    assert len(result) == 2


@pytest.mark.asyncio
async def test_count_with_filters(monkeypatch):
    from app.core.admin import admin as admin_module

    monkeypatch.setattr(admin_module, "select", lambda *a, **k: FakeSelect())

    async def fake_execute(self, query):
        return DummyResult(5)

    monkeypatch.setattr(DummySession, "execute", fake_execute, raising=False)

    crud = admin_module.BaseAdminCRUD(Model)
    count = await crud.count(DummySession(), filters={"field": "x"})
    assert count == 5


@pytest.mark.asyncio
async def test_get_not_found_and_delete_returns_false(monkeypatch):
    from app.core.admin import admin as admin_module

    monkeypatch.setattr(admin_module, "select", lambda *a, **k: FakeSelect())

    async def fake_execute(self, query):
        return DummyResult(None)

    monkeypatch.setattr(DummySession, "execute", fake_execute, raising=False)

    crud = admin_module.BaseAdminCRUD(Model)
    obj = await crud.get(DummySession(), record_id="missing")
    assert obj is None

    deleted = await crud.delete(DummySession(), record_id="missing")
    assert deleted is False
