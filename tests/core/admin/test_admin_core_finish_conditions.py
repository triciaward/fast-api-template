import types

import pytest
from pydantic import BaseModel

pytestmark = pytest.mark.unit


class DummySchema(BaseModel):
    field: int | None = None


@pytest.mark.asyncio
async def test_base_admin_update_with_dict_and_missing_fields(monkeypatch):
    from sqlalchemy import Column, Integer, String
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import declarative_base

    from app.core.admin.admin import BaseAdminCRUD

    Base = declarative_base()

    class M(Base):  # (test-only)
        __tablename__ = "t1"
        id = Column(String, primary_key=True)
        field = Column(Integer)

    crud = BaseAdminCRUD[M, DummySchema, DummySchema, DummySchema](M)

    class FakeResult:
        def __init__(self, obj):
            self._obj = obj

        def scalar_one_or_none(self):
            return self._obj

        def scalar(self):
            return 1

        def scalars(self):
            return types.SimpleNamespace(all=lambda: [self._obj] if self._obj else [])

    class FakeSession(AsyncSession):
        def __init__(self, obj):
            self._obj = obj
            self.commits = 0
            self.refreshed = 0

        async def execute(self, *a, **k):
            return FakeResult(self._obj)

        async def commit(self):
            self.commits += 1
            return

        async def refresh(self, obj):
            self.refreshed += 1
            return

        def add(self, obj):
            self._obj = obj
            return

        async def delete(self, obj):
            self._obj = None
            return

    obj = types.SimpleNamespace(id="1", field=1)
    db = FakeSession(obj)

    # update with dict path and attribute not present should be ignored
    updated = await crud.update(db, obj, {"field": 2, "missing": 3})
    assert updated.field == 2

    # count with filters only applies existing fields
    c = await crud.count(db, filters={"field": 2, "nope": True})
    assert isinstance(c, int)

    # delete returns True when found
    ok = await crud.delete(db, "1")
    assert ok is True

    # create path triggers commit and refresh
    created = await crud.create(db, DummySchema(field=5))
    assert db.commits >= 1 and db.refreshed >= 1 and getattr(created, "field", None) == 5

    # count returns 0 when scalar is None
    class FakeResultNone(FakeResult):
        def scalar(self):
            return None

    async def exec_none(*a, **k):
        return FakeResultNone(obj)

    db.execute = exec_none  # type: ignore[method-assign]
    assert await crud.count(db) == 0

    # get_multi without filters path
    res = await crud.get_multi(db, skip=0, limit=10, filters=None)
    assert isinstance(res, list)


def test_admin_only_endpoint_marks_function():
    from app.core.admin.admin import admin_only_endpoint

    def f():
        return 1

    g = admin_only_endpoint(f)
    assert getattr(g, "__admin_only__", False) is True


@pytest.mark.asyncio
async def test_admin_get_current_user_edge_cases(monkeypatch):
    from app.core.admin import admin as mod

    # sub missing
    monkeypatch.setattr(mod.jwt, "decode", lambda *a, **k: {"sub": None})
    with pytest.raises(Exception) as exc:
        await mod.get_current_user(token="tok", db=types.SimpleNamespace())
    assert "Could not validate credentials" in str(exc.value)

    # user not found
    monkeypatch.setattr(mod.jwt, "decode", lambda *a, **k: {"sub": "user1"})

    async def get_none(db, user_id):
        return None

    monkeypatch.setattr(mod, "get_db", lambda: types.SimpleNamespace())
    # Patch CRUD function import target
    import app.crud.auth.user as crud_user_mod

    monkeypatch.setattr(crud_user_mod, "get_user_by_id", get_none)
    with pytest.raises(Exception) as exc2:
        await mod.get_current_user(token="tok", db=types.SimpleNamespace())
    assert "Could not validate credentials" in str(exc2.value)
