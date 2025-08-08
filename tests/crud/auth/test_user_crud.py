import types

import pytest

from app.crud.auth import user as crud_user
from app.schemas.auth.user import UserCreate


class _ScalarOneOrNoneResult:
    def __init__(self, obj):  # type: ignore[no-untyped-def]
        self._obj = obj

    def scalar_one_or_none(self):  # type: ignore[no-untyped-def]
        return self._obj


class _ListScalarsResult:
    def __init__(self, items):  # type: ignore[no-untyped-def]
        self._items = items

    class _Scalars:
        def __init__(self, items):  # type: ignore[no-untyped-def]
            self._items = items

        def all(self):  # type: ignore[no-untyped-def]
            return self._items

    def scalars(self):  # type: ignore[no-untyped-def]
        return self._Scalars(self._items)


class _FakeSession:
    def __init__(self, result=None):  # type: ignore[no-untyped-def]
        self._result = result
        self.added = []
        self.deleted = []
        self.committed = False
        self.refreshed = []

    async def execute(self, *_args, **_kwargs):  # type: ignore[no-untyped-def]
        return self._result

    def add(self, obj):  # type: ignore[no-untyped-def]
        self.added.append(obj)

    async def commit(self):  # type: ignore[no-untyped-def]
        self.committed = True

    async def refresh(self, obj):  # type: ignore[no-untyped-def]
        self.refreshed.append(obj)

    async def delete(self, obj):  # type: ignore[no-untyped-def]
        self.deleted.append(obj)


pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_get_user_by_email_returns_user(monkeypatch):
    dummy_user = types.SimpleNamespace(id="u1", email="e@example.com", is_deleted=False)
    db = _FakeSession(result=_ScalarOneOrNoneResult(dummy_user))
    user = await crud_user.get_user_by_email(db, "e@example.com")
    assert user is dummy_user


@pytest.mark.asyncio
async def test_create_user_hashes_password_and_commits(monkeypatch):
    monkeypatch.setattr(crud_user, "get_password_hash", lambda p: "HASHED")
    db = _FakeSession()
    new_user = UserCreate(
        email="e@example.com",
        username="validuser",
        password="Password123!",
        is_superuser=False,
    )
    created = await crud_user.create_user(db, new_user)
    assert db.committed is True
    assert len(db.added) == 1
    assert created.email == "e@example.com"
    assert created.username == "validuser"
    assert created.hashed_password == "HASHED"


@pytest.mark.asyncio
async def test_authenticate_user_success_and_failure(monkeypatch):
    dummy_user = types.SimpleNamespace(hashed_password="HASH")

    async def fake_get_user_by_email(_db, _email):  # type: ignore[no-untyped-def]
        return dummy_user

    monkeypatch.setattr(crud_user, "get_user_by_email", fake_get_user_by_email)

    # Success
    monkeypatch.setattr(crud_user, "verify_password", lambda p, h: True)
    user_ok = await crud_user.authenticate_user(_FakeSession(), "e@example.com", "pw")
    assert user_ok is dummy_user

    # Failure
    monkeypatch.setattr(crud_user, "verify_password", lambda p, h: False)
    user_fail = await crud_user.authenticate_user(_FakeSession(), "e@example.com", "bad")
    assert user_fail is None


@pytest.mark.asyncio
async def test_update_user_password(monkeypatch):
    user_obj = types.SimpleNamespace(hashed_password="OLD")

    async def fake_get_user_by_id(_db, _id):  # type: ignore[no-untyped-def]
        return user_obj

    monkeypatch.setattr(crud_user, "get_user_by_id", fake_get_user_by_id)
    monkeypatch.setattr(crud_user, "get_password_hash", lambda p: "NEW_HASH")
    db = _FakeSession()
    ok = await crud_user.update_user_password(db, "u1", "newpass")
    assert ok is True
    assert user_obj.hashed_password == "NEW_HASH"
    assert db.committed is True


@pytest.mark.asyncio
async def test_soft_delete_and_restore_user(monkeypatch):
    # Soft delete uses get_user_by_id
    user_obj = types.SimpleNamespace(is_deleted=False, deleted_at=None)

    async def fake_get_user_by_id(_db, _id):  # type: ignore[no-untyped-def]
        return user_obj

    monkeypatch.setattr(crud_user, "get_user_by_id", fake_get_user_by_id)
    db = _FakeSession()
    ok = await crud_user.soft_delete_user(db, "u1")
    assert ok is True and user_obj.is_deleted is True

    # Restore uses get_user_by_id_any_status and checks flag
    user_obj.is_deleted = True

    async def fake_get_user_by_id_any_status(_db, _id):  # type: ignore[no-untyped-def]
        return user_obj

    monkeypatch.setattr(crud_user, "get_user_by_id_any_status", fake_get_user_by_id_any_status)
    ok2 = await crud_user.restore_user(db, "u1")
    assert ok2 is True and user_obj.is_deleted is False and user_obj.deleted_at is None


@pytest.mark.asyncio
async def test_permanently_delete_user(monkeypatch):
    user_obj = types.SimpleNamespace(id="u1")

    async def fake_get_user_by_id_any_status(_db, _id):  # type: ignore[no-untyped-def]
        return user_obj

    monkeypatch.setattr(crud_user, "get_user_by_id_any_status", fake_get_user_by_id_any_status)
    db = _FakeSession()
    ok = await crud_user.permanently_delete_user(db, "u1")
    assert ok is True
    assert db.deleted and db.deleted[0] is user_obj

import pytest

pytestmark = pytest.mark.template_only

def test_stub_user_crud() -> None:
    assert True
