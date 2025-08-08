import types

import pytest

pytestmark = pytest.mark.unit


class FakeResult:
    def __init__(self, value=None, many=None):
        self._value = value
        self._many = many

    def scalar_one_or_none(self):  # type: ignore[no-untyped-def]
        return self._value

    def scalars(self):  # type: ignore[no-untyped-def]
        return types.SimpleNamespace(all=lambda: self._many or [])


class FakeDB:
    def __init__(self, value=None, many=None):
        self.value = value
        self.many = many
        self.add_called = False
        self.commit_called = 0
        self.deleted = None

    async def execute(self, _):  # type: ignore[no-untyped-def]
        return FakeResult(self.value, self.many)

    async def commit(self):  # type: ignore[no-untyped-def]
        self.commit_called += 1

    async def refresh(self, _):  # type: ignore[no-untyped-def]
        return None

    def add(self, _):  # type: ignore[no-untyped-def]
        self.add_called = True

    async def delete(self, obj):  # type: ignore[no-untyped-def]
        self.deleted = obj


def _user(**over):
    base = dict(
        id="111",
        email="u@example.com",
        username="u",
        hashed_password="h",
        is_deleted=False,
        is_verified=False,
    )
    base.update(over)
    return types.SimpleNamespace(**base)


@pytest.mark.asyncio
async def test_get_user_by_email_none():
    from app.crud.auth import user as crud

    db = FakeDB(value=None)
    res = await crud.get_user_by_email(db, "x@example.com")
    assert res is None


@pytest.mark.asyncio
async def test_create_and_authenticate_user_success(monkeypatch):
    from app.crud.auth import user as crud

    db = FakeDB(value=None)

    # Create
    u = await crud.create_user(
        db,
        types.SimpleNamespace(
            email="e@x.com", username="e", password="Password123!", is_superuser=False,
        ),
    )
    assert db.add_called is True
    assert db.commit_called >= 1
    assert u.email == "e@x.com"

    # Authenticate should fetch by email and verify password
    # Simulate DB returning our user with hashed_password set by create_user
    db.value = u
    res = await crud.authenticate_user(db, "e@x.com", "Password123!")
    assert res is not None


@pytest.mark.asyncio
async def test_reset_and_update_password_paths(monkeypatch):
    from app.crud.auth import user as crud

    db = FakeDB(value=_user(id="222", hashed_password="old"))
    ok = await crud.reset_user_password(db, "222", "NewPass123!")
    assert ok is True
    assert db.commit_called >= 1

    db = FakeDB(value=_user(id="333", hashed_password="old"))
    ok = await crud.update_user_password(db, "333", "NewPass123!")
    assert ok is True


@pytest.mark.asyncio
async def test_soft_restore_permanent_delete(monkeypatch):
    from app.crud.auth import user as crud

    deleted_user = _user(id="444", is_deleted=True)
    db = FakeDB(value=_user(id="444", is_deleted=False))
    # soft delete
    ok = await crud.soft_delete_user(db, "444")
    assert ok is True
    assert db.commit_called >= 1

    # restore requires is_deleted True
    db = FakeDB(value=deleted_user)
    ok = await crud.restore_user(db, "444")
    assert ok is True

    # permanently delete
    db = FakeDB(value=deleted_user)
    ok = await crud.permanently_delete_user(db, "444")
    assert ok is True
