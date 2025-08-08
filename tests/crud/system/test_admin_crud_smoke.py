import types

import pytest

pytestmark = pytest.mark.unit


class DummyResult:
    def __init__(self, value=None):
        self._value = value

    def scalars(self):
        return types.SimpleNamespace(all=lambda: self._value or [])

    def scalar_one_or_none(self):
        return self._value

    def scalar(self):
        return 0


class DummySession:
    async def execute(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        return DummyResult([])

    async def add(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        return None

    async def commit(self):
        return None

    async def refresh(self, *args, **kwargs):
        return None

    async def delete(self, *args, **kwargs):
        return None


@pytest.mark.asyncio
async def test_admin_user_crud_list_deleted(monkeypatch):
    from app.crud.system.admin import AdminUserCRUD

    crud = AdminUserCRUD()
    users = await crud.get_deleted_users(DummySession(), skip=0, limit=10)
    assert isinstance(users, list)


@pytest.mark.asyncio
async def test_admin_user_statistics(monkeypatch):
    from app.crud.system.admin import AdminUserCRUD

    # Fake execute returns 0 for all counts
    class ResultZero:
        def scalar(self):
            return 0

    class SessionZero(DummySession):
        async def execute(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            return ResultZero()

    stats = await AdminUserCRUD().get_user_statistics(SessionZero())
    assert set(
        ["total_users", "superusers", "verified_users", "oauth_users", "deleted_users"]
    ).issubset(stats.keys())
