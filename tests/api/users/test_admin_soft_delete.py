import types
import uuid

import pytest

pytestmark = pytest.mark.unit


def _admin_user():
    return types.SimpleNamespace(
        id=uuid.UUID("00000000-0000-0000-0000-0000000000aa"),
        is_superuser=True,
        is_verified=True,
        is_deleted=False,
    )


def _deleted_user(idx: int = 1):
    created = "2025-01-01T00:00:00Z"
    deleted = "2025-01-02T00:00:00Z"
    # Ensure last segment is 12 hex digits (zero-padded)
    id_val = uuid.UUID(f"00000000-0000-0000-0000-{idx:012x}")
    return types.SimpleNamespace(
        id=id_val,
        email=f"u{idx}@example.com",
        username=f"user{idx}",
        is_superuser=False,
        is_verified=False,
        created_at=created,
        date_created=created,
        oauth_provider=None,
        is_deleted=True,
        deleted_at=deleted,
        deleted_by=_admin_user().id,
        deletion_reason="cleanup",
    )


@pytest.mark.asyncio
async def test_soft_delete_user_happy(monkeypatch, async_client):
    from app.api.users import admin as user_admin_module
    from app.crud.auth import user as crud_user
    from app.main import app

    app.dependency_overrides[user_admin_module.get_current_user] = lambda: _admin_user()

    calls = {"n": 0}

    async def fake_get_user_by_id(db, user_id):
        calls["n"] += 1
        if calls["n"] == 1:
            return types.SimpleNamespace(id=user_id, is_deleted=False)
        # second call returns deleted metadata that matches schema
        return _deleted_user(1)

    async def fake_soft_delete_user(db, user_id):
        return True

    monkeypatch.setattr(crud_user, "get_user_by_id", fake_get_user_by_id)
    monkeypatch.setattr(crud_user, "soft_delete_user", fake_soft_delete_user)

    r = await async_client.request(
        "DELETE",
        "/users/00000000-0000-0000-0000-000000000001/soft",
        json={"reason": "testing"},
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert r.status_code == 200
    body = r.json()
    assert body["message"].startswith("User soft deleted")


@pytest.mark.asyncio
async def test_soft_delete_user_not_found(monkeypatch, async_client):
    from app.api.users import admin as user_admin_module
    from app.crud.auth import user as crud_user
    from app.main import app

    app.dependency_overrides[user_admin_module.get_current_user] = lambda: _admin_user()

    async def fake_get_user_by_id(db, user_id):
        return None

    monkeypatch.setattr(crud_user, "get_user_by_id", fake_get_user_by_id)

    r = await async_client.request(
        "DELETE",
        "/users/00000000-0000-0000-0000-000000000002/soft",
        json={"reason": "nope"},
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_restore_user_flow(monkeypatch, async_client):
    from app.api.users import admin as user_admin_module
    from app.crud.auth import user as crud_user
    from app.main import app

    app.dependency_overrides[user_admin_module.get_current_user] = lambda: _admin_user()

    async def fake_get_user_by_id(db, user_id):
        return types.SimpleNamespace(id=user_id, is_deleted=True)

    async def fake_restore_user(db, user_id):
        return True

    monkeypatch.setattr(crud_user, "get_user_by_id", fake_get_user_by_id)
    monkeypatch.setattr(crud_user, "restore_user", fake_restore_user)

    r = await async_client.post(
        "/users/00000000-0000-0000-0000-000000000003/restore",
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert r.status_code == 200
    assert r.json()["message"].startswith("User restored")


@pytest.mark.asyncio
async def test_list_deleted_users(monkeypatch, async_client):
    from app.api.users import admin as user_admin_module
    from app.main import app

    app.dependency_overrides[user_admin_module.get_current_user] = lambda: _admin_user()

    async def fake_get_deleted_users(db, skip, limit):
        return [_deleted_user(1), _deleted_user(2)]

    async def fake_count_deleted_users(db):
        return 2

    monkeypatch.setattr(user_admin_module.admin_user_crud, "get_deleted_users", fake_get_deleted_users)
    monkeypatch.setattr(user_admin_module.admin_user_crud, "count_deleted_users", fake_count_deleted_users)

    r = await async_client.get(
        "/users/deleted?page=1&size=2",
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert r.status_code == 200
    body = r.json()
    assert body["metadata"]["total"] == 2
    assert len(body["items"]) == 2


@pytest.mark.asyncio
async def test_search_deleted_users(monkeypatch, async_client):
    from app.api.users import admin as user_admin_module
    from app.main import app

    app.dependency_overrides[user_admin_module.get_current_user] = lambda: _admin_user()

    async def fake_get_deleted_users(db, skip, limit):
        return [_deleted_user(1)]

    async def fake_count_deleted_users(db):
        return 1

    monkeypatch.setattr(user_admin_module.admin_user_crud, "get_deleted_users", fake_get_deleted_users)
    monkeypatch.setattr(user_admin_module.admin_user_crud, "count_deleted_users", fake_count_deleted_users)

    r = await async_client.get(
        "/users/deleted/search?deletion_reason=cleanup",
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert r.status_code == 200
    body = r.json()
    assert body["filters_applied"]


@pytest.mark.asyncio
async def test_permanently_delete_user_success(monkeypatch, async_client):
    from app.api.users import admin as user_admin_module
    from app.crud.auth import user as crud_user
    from app.main import app

    app.dependency_overrides[user_admin_module.get_current_user] = lambda: _admin_user()

    async def fake_get_user_by_id(db, user_id):
        return types.SimpleNamespace(id=user_id)

    async def fake_permanent_delete(db, user_id):
        return True

    monkeypatch.setattr(crud_user, "get_user_by_id", fake_get_user_by_id)
    monkeypatch.setattr(crud_user, "permanently_delete_user", fake_permanent_delete)

    r = await async_client.request(
        "DELETE",
        "/users/00000000-0000-0000-0000-000000000004/permanent",
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert r.status_code == 204
