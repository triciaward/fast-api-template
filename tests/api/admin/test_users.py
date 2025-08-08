import types

import pytest

pytestmark = pytest.mark.unit


def _admin_user(id_suffix: str = "1", is_superuser: bool = True):
    return types.SimpleNamespace(
        id=f"00000000-0000-0000-0000-00000000000{id_suffix}",
        email=f"a{id_suffix}@example.com",
        username=f"admin{id_suffix}",
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
async def test_admin_list_requires_superuser(monkeypatch, async_client):
    # Use dependency override to return a non-superuser directly
    from app.core.admin import admin as core_admin_module
    from app.main import app

    async def fake_get_current_user():  # type: ignore[no-untyped-def]
        return _admin_user("9", is_superuser=False)

    app.dependency_overrides[core_admin_module.get_current_user] = fake_get_current_user

    resp = await async_client.get(
        "/admin/users",
        headers={"authorization": "Bearer dummy", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_list_success(monkeypatch, async_client):
    # Override to return a valid superuser
    from app.core.admin import admin as core_admin_module
    from app.main import app

    async def fake_get_current_user():  # type: ignore[no-untyped-def]
        return _admin_user("8", is_superuser=True)

    app.dependency_overrides[core_admin_module.get_current_user] = fake_get_current_user

    # Mock CRUD to return users and count
    from app.api.admin import users as admin_users_module

    async def fake_get_users(db, skip, limit, **kwargs):
        return [_admin_user("1"), _admin_user("2")]

    async def fake_count(db, **kwargs):
        return 2

    monkeypatch.setattr(admin_users_module.admin_user_crud, "get_users", fake_get_users)
    monkeypatch.setattr(admin_users_module.admin_user_crud, "count", fake_count)

    resp = await async_client.get(
        "/admin/users",
        headers={"authorization": "Bearer dummy", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert resp.status_code == 200
    data = resp.json()
    assert data["metadata"]["total"] == 2
    assert len(data["items"]) == 2
