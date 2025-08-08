import types
import uuid

import pytest

pytestmark = pytest.mark.unit


def _admin():
    return types.SimpleNamespace(id=uuid.UUID("00000000-0000-0000-0000-0000000000aa"))


@pytest.mark.asyncio
async def test_list_users_with_all_filters(monkeypatch, async_client):
    from app.api.admin import users as mod
    from app.main import app

    app.dependency_overrides[mod.require_superuser] = lambda: _admin()

    async def fake_get_users(db, skip, limit, is_superuser, is_verified, is_deleted, oauth_provider):
        assert is_superuser is True
        assert is_verified is False
        assert is_deleted is True
        assert oauth_provider == "google"
        return [types.SimpleNamespace(
            id=uuid.uuid4(), email="a@example.com", username="axxx", is_superuser=True,
            is_verified=False, is_deleted=True, created_at="2025-01-01T00:00:00Z",
            oauth_provider="google", oauth_id=None, oauth_email=None,
            deletion_requested_at=None, deletion_confirmed_at=None, deletion_scheduled_for=None,
        )]

    async def fake_count(db, filters):
        assert filters == {
            "is_superuser": True,
            "is_verified": False,
            "is_deleted": True,
            "oauth_provider": "google",
        }
        return 1

    monkeypatch.setattr(mod.admin_user_crud, "get_users", fake_get_users)
    monkeypatch.setattr(mod.admin_user_crud, "count", fake_count)

    r = await async_client.get("/admin/users?is_superuser=true&is_verified=false&is_deleted=true&oauth_provider=google")
    app.dependency_overrides.clear()
    assert r.status_code == 200
    assert r.json()["metadata"]["total"] == 1


@pytest.mark.asyncio
async def test_get_user_success(monkeypatch, async_client):
    from app.api.admin import users as mod
    from app.main import app

    app.dependency_overrides[mod.require_superuser] = lambda: _admin()

    uid = uuid.uuid4()

    async def fake_get(db, user_id):
        return types.SimpleNamespace(
            id=uid, email="x@example.com", username="userx", is_superuser=False,
            is_verified=True, is_deleted=False, created_at="2025-01-01T00:00:00Z",
            oauth_provider=None, oauth_id=None, oauth_email=None,
            deletion_requested_at=None, deletion_confirmed_at=None, deletion_scheduled_for=None,
        )

    monkeypatch.setattr(mod.admin_user_crud, "get", fake_get)

    r = await async_client.get(f"/admin/users/{uid}")
    app.dependency_overrides.clear()
    assert r.status_code == 200
    assert r.json()["id"] == str(uid)


@pytest.mark.asyncio
async def test_force_delete_user_success(monkeypatch, async_client):
    from app.api.admin import users as mod
    from app.main import app

    app.dependency_overrides[mod.require_superuser] = lambda: _admin()

    async def fake_get(db, user_id):
        return object()

    async def fake_force(db, user_id):
        return True

    monkeypatch.setattr(mod.admin_user_crud, "get", fake_get)
    monkeypatch.setattr(mod.admin_user_crud, "force_delete_user", fake_force)

    r = await async_client.post(f"/admin/users/{uuid.uuid4()}/force-delete")
    app.dependency_overrides.clear()
    assert r.status_code == 204
