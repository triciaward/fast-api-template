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
    )


def _user(uid: int, superuser: bool = False, verified: bool = True):
    return types.SimpleNamespace(
        id=UUID(f"00000000-0000-0000-0000-00000000000{uid}"),
        is_superuser=superuser,
        is_verified=verified,
    )


@pytest.mark.asyncio
async def test_toggle_superuser_success(monkeypatch, async_client):
    from app.api.admin import users as admin_users
    from app.core.admin import admin as core_admin_module
    from app.main import app

    app.dependency_overrides[core_admin_module.get_current_user] = lambda: _admin_user(True)

    async def fake_toggle(db, uid):
        return _user(2, superuser=True)

    monkeypatch.setattr(admin_users.admin_user_crud, "toggle_superuser_status", fake_toggle)

    resp = await async_client.post(
        "/admin/users/00000000-0000-0000-0000-000000000002/toggle-superuser",
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == "00000000-0000-0000-0000-000000000002"
    assert data["field"] == "is_superuser"
    assert data["new_value"] is True


@pytest.mark.asyncio
async def test_toggle_superuser_not_found(monkeypatch, async_client):
    from app.api.admin import users as admin_users
    from app.core.admin import admin as core_admin_module
    from app.main import app

    app.dependency_overrides[core_admin_module.get_current_user] = lambda: _admin_user(True)

    async def fake_toggle(db, uid):
        return None

    monkeypatch.setattr(admin_users.admin_user_crud, "toggle_superuser_status", fake_toggle)

    resp = await async_client.post(
        "/admin/users/00000000-0000-0000-0000-000000000099/toggle-superuser",
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_toggle_verification_success(monkeypatch, async_client):
    from app.api.admin import users as admin_users
    from app.core.admin import admin as core_admin_module
    from app.main import app

    app.dependency_overrides[core_admin_module.get_current_user] = lambda: _admin_user(True)

    async def fake_toggle(db, uid):
        return _user(3, verified=False)

    monkeypatch.setattr(admin_users.admin_user_crud, "toggle_verification_status", fake_toggle)

    resp = await async_client.post(
        "/admin/users/00000000-0000-0000-0000-000000000003/toggle-verification",
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == "00000000-0000-0000-0000-000000000003"
    assert data["field"] == "is_verified"
    assert data["new_value"] is False


@pytest.mark.asyncio
async def test_toggle_verification_not_found(monkeypatch, async_client):
    from app.api.admin import users as admin_users
    from app.core.admin import admin as core_admin_module
    from app.main import app

    app.dependency_overrides[core_admin_module.get_current_user] = lambda: _admin_user(True)

    async def fake_toggle(db, uid):
        return None

    monkeypatch.setattr(admin_users.admin_user_crud, "toggle_verification_status", fake_toggle)

    resp = await async_client.post(
        "/admin/users/00000000-0000-0000-0000-000000000098/toggle-verification",
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_bulk_operations_verify_mixed(monkeypatch, async_client):
    from app.api.admin import users as admin_users
    from app.core.admin import admin as core_admin_module
    from app.main import app

    app.dependency_overrides[core_admin_module.get_current_user] = lambda: _admin_user(True)

    calls = {"count": 0}

    async def fake_toggle_verification(db, uid):
        calls["count"] += 1
        # Fail every second call
        if calls["count"] % 2 == 0:
            return None
        # Simulate that the function toggles but may need a second call; endpoint calls twice in some cases
        return _user(10, verified=False)

    monkeypatch.setattr(admin_users.admin_user_crud, "toggle_verification_status", fake_toggle_verification)

    req = {
        "operation": "verify",
        "user_ids": [
            "00000000-0000-0000-0000-000000000010",
            "00000000-0000-0000-0000-000000000011",
            "00000000-0000-0000-0000-000000000012",
            "00000000-0000-0000-0000-000000000013",
        ],
    }

    resp = await async_client.post(
        "/admin/bulk-operations",
        json=req,
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert resp.status_code == 200
    data = resp.json()
    assert data["operation"] == "verify"
    assert data["total_users"] == 4
    assert data["successful"] + data["failed"] == 4


@pytest.mark.asyncio
async def test_bulk_operations_unverify_counts(monkeypatch, async_client):
    from app.api.admin import users as admin_users
    from app.core.admin import admin as core_admin_module
    from app.main import app

    app.dependency_overrides[core_admin_module.get_current_user] = lambda: _admin_user(True)

    async def fake_toggle_verification(db, uid):
        # Return a user each call; when operation is unverify, endpoint will call twice to flip correctly
        return _user(20, verified=True)

    monkeypatch.setattr(admin_users.admin_user_crud, "toggle_verification_status", fake_toggle_verification)

    req = {
        "operation": "unverify",
        "user_ids": [
            "00000000-0000-0000-0000-000000000020",
            "00000000-0000-0000-0000-000000000021",
        ],
    }

    resp = await async_client.post(
        "/admin/bulk-operations",
        json=req,
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert resp.status_code == 200
    data = resp.json()
    assert data["operation"] == "unverify"
    assert data["total_users"] == 2
    assert data["successful"] + data["failed"] == 2


