import types
from typing import Any

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
        return 0


class DummySession:
    async def execute(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        return DummyResult([])

    def add(self, *args, **kwargs):
        return None

    async def commit(self):
        return None

    async def refresh(self, *args, **kwargs):
        return None

    async def delete(self, *args, **kwargs):
        return None


@pytest.mark.asyncio
async def test_get_user_by_email_and_username(monkeypatch):
    from app.crud.system.admin import AdminUserCRUD

    class Once(DummySession):
        async def execute(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            return DummyResult(types.SimpleNamespace(id="u1"))

    db = Once()
    crud = AdminUserCRUD()
    u1 = await crud.get_user_by_email(db, "a@example.com")
    u2 = await crud.get_user_by_username(db, "alice")
    assert u1 and u2


@pytest.mark.asyncio
async def test_toggle_flags_no_user_returns_none():
    from app.crud.system.admin import AdminUserCRUD

    crud = AdminUserCRUD()
    user = await crud.toggle_superuser_status(DummySession(), "missing")
    assert user is None

    user2 = await crud.toggle_verification_status(DummySession(), "missing")
    assert user2 is None


@pytest.mark.asyncio
async def test_get_users_filter_propagation(monkeypatch):
    from app.crud.system.admin import AdminUserCRUD

    captured: dict[str, Any] = {}

    async def fake_get_multi(self, db, skip, limit, filters=None):  # type: ignore[no-untyped-def]
        captured.update({"skip": skip, "limit": limit, "filters": filters or {}})
        return []

    monkeypatch.setattr(AdminUserCRUD, "get_multi", fake_get_multi, raising=False)

    crud = AdminUserCRUD()
    _ = await crud.get_users(
        DummySession(),
        skip=5,
        limit=7,
        is_superuser=True,
        is_verified=False,
        is_deleted=False,
        oauth_provider="google",
    )
    assert captured["skip"] == 5 and captured["limit"] == 7
    assert captured["filters"] == {
        "is_superuser": True,
        "is_verified": False,
        "is_deleted": False,
        "oauth_provider": "google",
    }


@pytest.mark.asyncio
async def test_toggle_flags_with_user(monkeypatch):
    from app.crud.system.admin import AdminUserCRUD

    # Provide an existing user and ensure toggles flip values
    user_obj = types.SimpleNamespace(id="u1", is_superuser=False, is_verified=False)

    async def fake_get(self, db, user_id):  # type: ignore[no-untyped-def]
        return user_obj

    monkeypatch.setattr(AdminUserCRUD, "get", fake_get, raising=False)

    class Sess(DummySession):
        async def commit(self):  # type: ignore[no-untyped-def]
            return None

        async def refresh(self, *a, **k):  # type: ignore[no-untyped-def]
            return None

    db = Sess()
    updated = await AdminUserCRUD().toggle_superuser_status(db, "u1")
    assert updated and updated.is_superuser is True

    updated2 = await AdminUserCRUD().toggle_verification_status(db, "u1")
    assert updated2 and updated2.is_verified is True


@pytest.mark.asyncio
async def test_delete_user_wrapper(monkeypatch):
    from app.crud.system.admin import AdminUserCRUD

    async def fake_delete(self, db, user_id):  # type: ignore[no-untyped-def]
        return True

    monkeypatch.setattr(AdminUserCRUD, "delete", fake_delete, raising=False)
    ok = await AdminUserCRUD().delete_user(DummySession(), "u1")
    assert ok is True


@pytest.mark.asyncio
async def test_force_delete_user_calls_soft_delete(monkeypatch):
    from app.crud.auth import user as crud_user
    from app.crud.system.admin import AdminUserCRUD

    called = {"n": 0}

    async def fake_soft_delete_user(db, user_id):  # type: ignore[no-untyped-def]
        called["n"] += 1
        return True

    monkeypatch.setattr(
        crud_user,
        "soft_delete_user",
        fake_soft_delete_user,
        raising=False,
    )
    ok = await AdminUserCRUD().force_delete_user(DummySession(), "u1")
    assert ok is True and called["n"] == 1


@pytest.mark.asyncio
async def test_count_deleted_users_filters(monkeypatch):
    from app.crud.system.admin import AdminUserCRUD

    captured: dict[str, Any] = {}

    async def fake_count(self, db, filters=None):  # type: ignore[no-untyped-def]
        captured["filters"] = filters or {}
        return 3

    monkeypatch.setattr(AdminUserCRUD, "count", fake_count, raising=False)
    n = await AdminUserCRUD().count_deleted_users(DummySession())
    assert n == 3 and captured["filters"] == {"is_deleted": True}
