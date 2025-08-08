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


@pytest.mark.asyncio
async def test_get_user_not_found(monkeypatch, async_client):
    from app.api.admin import users as admin_users_module
    from app.core.admin import admin as core_admin_module
    from app.main import app

    async def fake_get_current_user():  # type: ignore[no-untyped-def]
        return _admin_user(True)

    app.dependency_overrides[core_admin_module.get_current_user] = fake_get_current_user

    async def fake_get(db, user_id):
        return None

    monkeypatch.setattr(admin_users_module.admin_user_crud, "get", fake_get)

    resp = await async_client.get(
        "/admin/users/11111111-1111-1111-1111-111111111111",
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_toggle_superuser_self_block(monkeypatch, async_client):
    from app.core.admin import admin as core_admin_module
    from app.main import app

    current_admin = _admin_user(True)

    async def fake_get_current_user():  # type: ignore[no-untyped-def]
        return current_admin

    app.dependency_overrides[core_admin_module.get_current_user] = fake_get_current_user

    resp = await async_client.post(
        f"/admin/users/{current_admin.id}/toggle-superuser",
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert resp.status_code == 400
    assert "cannot modify your own" in resp.json()["error"]["message"].lower()
