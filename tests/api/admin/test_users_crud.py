import types
from uuid import UUID

import pytest

pytestmark = pytest.mark.unit


def _admin_user(is_superuser: bool = True):
    return types.SimpleNamespace(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        email="admin@example.com",
        username="admin",
        is_superuser=is_superuser,
        is_verified=True,
        is_deleted=False,
        created_at="2025-01-01T00:00:00Z",
        oauth_provider=None,
        oauth_id=None,
        oauth_email=None,
        deletion_requested_at=None,
        deletion_confirmed_at=None,
        deletion_scheduled_for=None,
    )


def _user(idx: int = 1, verified: bool = True, superuser: bool = False):
    return types.SimpleNamespace(
        id=UUID(f"00000000-0000-0000-0000-00000000000{idx}"),
        email=f"u{idx}@example.com",
        username=f"user{idx}",
        is_superuser=superuser,
        is_verified=verified,
        is_deleted=False,
        created_at="2025-01-01T00:00:00Z",
        date_created="2025-01-01T00:00:00Z",
        oauth_provider=None,
        oauth_id=None,
        oauth_email=None,
        deletion_requested_at=None,
        deletion_confirmed_at=None,
        deletion_scheduled_for=None,
    )


@pytest.mark.asyncio
async def test_admin_create_user_conflict_email(monkeypatch, async_client):
    from app.api.admin import users as admin_users
    from app.core.admin import admin as core_admin_module
    from app.main import app

    app.dependency_overrides[core_admin_module.get_current_user] = lambda: _admin_user(
        True,
    )

    async def fake_get_user_by_email(db, email):
        return _user(1)

    monkeypatch.setattr(
        admin_users.admin_user_crud,
        "get_user_by_email",
        fake_get_user_by_email,
    )

    resp = await async_client.post(
        "/admin/users",
        json={
            "email": "new@example.com",
            "username": "validuser",
            "password": "Password123!",
            "is_superuser": False,
        },
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_admin_create_user_success(monkeypatch, async_client):
    from app.api.admin import users as admin_users
    from app.core.admin import admin as core_admin_module
    from app.main import app

    app.dependency_overrides[core_admin_module.get_current_user] = lambda: _admin_user(
        True,
    )

    async def fake_get_user_by_email(db, email):
        return None

    async def fake_get_user_by_username(db, username):
        return None

    monkeypatch.setattr(
        admin_users.admin_user_crud,
        "get_user_by_email",
        fake_get_user_by_email,
    )
    monkeypatch.setattr(
        admin_users.admin_user_crud,
        "get_user_by_username",
        fake_get_user_by_username,
    )

    async def fake_create_user(db, user_create):
        return _user(2)

    monkeypatch.setattr(admin_users.admin_user_crud, "create_user", fake_create_user)

    resp = await async_client.post(
        "/admin/users",
        json={
            "email": "ok@example.com",
            "username": "validuser",
            "password": "Password123!",
            "is_superuser": True,
        },
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "u2@example.com"


@pytest.mark.asyncio
async def test_admin_update_user_conflict_email(monkeypatch, async_client):
    from app.api.admin import users as admin_users
    from app.core.admin import admin as core_admin_module
    from app.main import app

    app.dependency_overrides[core_admin_module.get_current_user] = lambda: _admin_user(
        True,
    )

    async def fake_get(db, uid):
        return _user(3)

    async def fake_get_user_by_email(db, email):
        return _user(9)

    monkeypatch.setattr(admin_users.admin_user_crud, "get", fake_get)
    monkeypatch.setattr(
        admin_users.admin_user_crud,
        "get_user_by_email",
        fake_get_user_by_email,
    )

    resp = await async_client.put(
        "/admin/users/00000000-0000-0000-0000-000000000003",
        json={"email": "exists@example.com"},
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_admin_update_user_success(monkeypatch, async_client):
    from app.api.admin import users as admin_users
    from app.core.admin import admin as core_admin_module
    from app.main import app

    app.dependency_overrides[core_admin_module.get_current_user] = lambda: _admin_user(
        True,
    )

    async def fake_get(db, uid):
        return _user(4)

    async def fake_get_user_by_email(db, email):
        return None

    async def fake_get_user_by_username(db, username):
        return None

    monkeypatch.setattr(admin_users.admin_user_crud, "get", fake_get)
    monkeypatch.setattr(
        admin_users.admin_user_crud,
        "get_user_by_email",
        fake_get_user_by_email,
    )
    monkeypatch.setattr(
        admin_users.admin_user_crud,
        "get_user_by_username",
        fake_get_user_by_username,
    )

    async def fake_update_user(db, uid, user_update):
        u = _user(4)
        u.username = "updated"
        return u

    monkeypatch.setattr(admin_users.admin_user_crud, "update_user", fake_update_user)

    resp = await async_client.put(
        "/admin/users/00000000-0000-0000-0000-000000000004",
        json={"username": "updated"},
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert resp.json()["username"] == "updated"


@pytest.mark.asyncio
async def test_admin_delete_user_self_block(monkeypatch, async_client):
    from app.core.admin import admin as core_admin_module
    from app.main import app

    admin = _admin_user(True)
    app.dependency_overrides[core_admin_module.get_current_user] = lambda: admin

    resp = await async_client.delete(
        f"/admin/users/{admin.id}",
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_admin_delete_user_success(monkeypatch, async_client):
    from app.api.admin import users as admin_users
    from app.core.admin import admin as core_admin_module
    from app.main import app

    app.dependency_overrides[core_admin_module.get_current_user] = lambda: _admin_user(
        True,
    )

    async def fake_get(db, uid):
        return _user(5)

    async def fake_delete_user(db, uid):
        return True

    monkeypatch.setattr(admin_users.admin_user_crud, "get", fake_get)
    monkeypatch.setattr(admin_users.admin_user_crud, "delete_user", fake_delete_user)

    resp = await async_client.delete(
        "/admin/users/00000000-0000-0000-0000-000000000005",
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_admin_statistics(monkeypatch, async_client):
    from app.api.admin import users as admin_users
    from app.core.admin import admin as core_admin_module
    from app.main import app

    app.dependency_overrides[core_admin_module.get_current_user] = lambda: _admin_user(
        True,
    )

    stats = {
        "total_users": 10,
        "superusers": 1,
        "verified_users": 8,
        "oauth_users": 2,
        "deleted_users": 0,
        "regular_users": 9,
        "unverified_users": 2,
    }

    async def fake_get_user_statistics(db):
        return stats

    monkeypatch.setattr(
        admin_users.admin_user_crud,
        "get_user_statistics",
        fake_get_user_statistics,
    )

    resp = await async_client.get(
        "/admin/statistics",
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert resp.json()["total_users"] == 10
