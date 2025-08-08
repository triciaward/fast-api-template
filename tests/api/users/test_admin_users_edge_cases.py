import types
import uuid

import pytest

pytestmark = pytest.mark.unit


def _user():
    return types.SimpleNamespace(id=uuid.UUID("00000000-0000-0000-0000-0000000000bb"))


@pytest.mark.asyncio
async def test_soft_delete_failure_returns_500(monkeypatch, async_client):
    from app.api.users import admin as mod
    from app.main import app

    app.dependency_overrides[mod.get_current_user] = lambda: _user()

    async def get_user_by_id(db, uid):
        return types.SimpleNamespace(id=uid, is_deleted=False)

    async def soft_delete_user(db, user_id):
        return False

    monkeypatch.setattr(mod.crud_user, "get_user_by_id", get_user_by_id)
    monkeypatch.setattr(mod.crud_user, "soft_delete_user", soft_delete_user)

    r = await async_client.request(
        "DELETE", f"/users/{uuid.uuid4()}/soft", json={"reason": "cleanup"}
    )
    app.dependency_overrides.clear()
    assert r.status_code == 500


@pytest.mark.asyncio
async def test_restore_user_not_found_returns_404(monkeypatch, async_client):
    from app.api.users import admin as mod
    from app.main import app

    app.dependency_overrides[mod.get_current_user] = lambda: _user()

    async def get_user_by_id_none(db, uid):
        return None

    monkeypatch.setattr(mod.crud_user, "get_user_by_id", get_user_by_id_none)

    r = await async_client.post(f"/users/{uuid.uuid4()}/restore")
    app.dependency_overrides.clear()
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_restore_user_failure_returns_500(monkeypatch, async_client):
    from app.api.users import admin as mod
    from app.main import app

    app.dependency_overrides[mod.get_current_user] = lambda: _user()

    async def get_user_by_id_deleted(db, uid):
        return types.SimpleNamespace(id=uid, is_deleted=True)

    async def restore_user_fail(db, user_id):
        return False

    monkeypatch.setattr(mod.crud_user, "get_user_by_id", get_user_by_id_deleted)
    monkeypatch.setattr(mod.crud_user, "restore_user", restore_user_fail)

    r = await async_client.post(f"/users/{uuid.uuid4()}/restore")
    app.dependency_overrides.clear()
    assert r.status_code == 500


@pytest.mark.asyncio
async def test_permanently_delete_user_failure_returns_500(monkeypatch, async_client):
    from app.api.users import admin as mod
    from app.main import app

    app.dependency_overrides[mod.get_current_user] = lambda: _user()

    async def get_user_by_id_ok(db, uid):
        return types.SimpleNamespace(id=uid)

    async def permanent_fail(db, user_id):
        return False

    monkeypatch.setattr(mod.crud_user, "get_user_by_id", get_user_by_id_ok)
    monkeypatch.setattr(mod.crud_user, "permanently_delete_user", permanent_fail)

    r = await async_client.delete(f"/users/{uuid.uuid4()}/permanent")
    app.dependency_overrides.clear()
    assert r.status_code == 500
