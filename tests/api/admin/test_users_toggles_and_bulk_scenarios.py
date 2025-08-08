import types

import pytest

pytestmark = pytest.mark.unit


def _admin_user():
    return types.SimpleNamespace(
        id="00000000-0000-0000-0000-0000000000aa",
        is_superuser=True,
        is_verified=True,
        is_deleted=False,
    )


@pytest.mark.asyncio
async def test_force_delete_user_not_found(monkeypatch, async_client):
    from app.api.admin import users as admin_users
    from app.core.admin import admin as core_admin_module
    from app.main import app

    app.dependency_overrides[core_admin_module.get_current_user] = lambda: _admin_user()

    async def fake_get(db, uid):
        return None

    monkeypatch.setattr(admin_users.admin_user_crud, "get", fake_get)

    r = await async_client.post(
        "/admin/users/00000000-0000-0000-0000-00000000fff0/force-delete",
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_force_delete_user_internal_error(monkeypatch, async_client):
    from app.api.admin import users as admin_users
    from app.core.admin import admin as core_admin_module
    from app.main import app

    app.dependency_overrides[core_admin_module.get_current_user] = lambda: _admin_user()

    async def fake_get(db, uid):
        return types.SimpleNamespace(id=uid)

    async def fake_force_delete(db, uid):
        return False

    monkeypatch.setattr(admin_users.admin_user_crud, "get", fake_get)
    monkeypatch.setattr(
        admin_users.admin_user_crud, "force_delete_user", fake_force_delete
    )

    r = await async_client.post(
        "/admin/users/00000000-0000-0000-0000-00000000fff1/force-delete",
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert r.status_code == 500


@pytest.mark.asyncio
async def test_bulk_operations_invalid_operation(monkeypatch, async_client):
    from app.core.admin import admin as core_admin_module
    from app.main import app

    app.dependency_overrides[core_admin_module.get_current_user] = lambda: _admin_user()

    r = await async_client.post(
        "/admin/bulk-operations",
        json={
            "operation": "noop",
            "user_ids": ["00000000-0000-0000-0000-000000000001"],
        },
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    # Schema should reject invalid operation with a 422 validation error
    assert r.status_code == 422
    assert r.json()["error"]["type"] == "ValidationError"
