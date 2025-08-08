import types

import pytest

pytestmark = pytest.mark.unit


class DummySession:
    def __init__(self):
        self.added = []

    async def execute(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        class R:
            def scalar_one_or_none(self):
                return types.SimpleNamespace(id="u1", is_superuser=False)
        return R()

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        return None

    async def refresh(self, *args, **kwargs):
        return None


@pytest.mark.asyncio
async def test_create_user_hashes_password(monkeypatch):
    from app.crud.system import admin as admin_mod
    from app.crud.system.admin import AdminUserCRUD
    from app.schemas.auth.user import UserCreate

    # Force hashing to a known value in the module under test
    monkeypatch.setattr(admin_mod, "get_password_hash", lambda p: "hashed")

    db = DummySession()
    user = await AdminUserCRUD().create_user(db, UserCreate(email="a@b.com", username="alice", password="Password123!"))
    # ensure object was added and has hashed_password assigned
    assert db.added and getattr(user, "hashed_password", None) == "hashed"


@pytest.mark.asyncio
async def test_update_user_password_hashes_when_included(monkeypatch):
    from app.crud.system import admin as admin_mod
    from app.crud.system.admin import AdminUserCRUD
    from app.schemas.admin.admin import AdminUserUpdate

    # Stub BaseAdminCRUD.get to return a minimal user object with existing hashed_password attribute
    user_obj = types.SimpleNamespace(id="u1", is_superuser=False, hashed_password="old")

    async def fake_get(self, db, user_id):
        return user_obj

    monkeypatch.setattr(AdminUserCRUD, "get", fake_get)  # type: ignore[arg-type]
    monkeypatch.setattr(admin_mod, "get_password_hash", lambda p: "hashed2")

    db = DummySession()
    updated = await AdminUserCRUD().update_user(db, "u1", AdminUserUpdate(password="NewPassword456!"))
    assert getattr(updated, "hashed_password", None) == "hashed2"
