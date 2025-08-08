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


@pytest.mark.asyncio
async def test_soft_delete_user_already_deleted(monkeypatch, async_client):
    from app.api.users import admin as user_admin_module
    from app.crud.auth import user as crud_user
    from app.main import app

    app.dependency_overrides[user_admin_module.get_current_user] = lambda: _admin_user()

    async def fake_get_user_by_id(db, user_id):
        return types.SimpleNamespace(id=user_id, is_deleted=True)

    monkeypatch.setattr(crud_user, "get_user_by_id", fake_get_user_by_id)

    r = await async_client.request(
        "DELETE",
        "/users/00000000-0000-0000-0000-000000000010/soft",
        json={"reason": "already"},
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_restore_user_not_deleted(monkeypatch, async_client):
    from app.api.users import admin as user_admin_module
    from app.crud.auth import user as crud_user
    from app.main import app

    app.dependency_overrides[user_admin_module.get_current_user] = lambda: _admin_user()

    async def fake_get_user_by_id(db, user_id):
        return types.SimpleNamespace(id=user_id, is_deleted=False)

    monkeypatch.setattr(crud_user, "get_user_by_id", fake_get_user_by_id)

    r = await async_client.post(
        "/users/00000000-0000-0000-0000-000000000011/restore",
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_permanently_delete_user_not_found(monkeypatch, async_client):
    from app.api.users import admin as user_admin_module
    from app.crud.auth import user as crud_user
    from app.main import app

    app.dependency_overrides[user_admin_module.get_current_user] = lambda: _admin_user()

    async def fake_get_user_by_id(db, user_id):
        return None

    monkeypatch.setattr(crud_user, "get_user_by_id", fake_get_user_by_id)

    r = await async_client.request(
        "DELETE",
        "/users/00000000-0000-0000-0000-000000000012/permanent",
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_permanently_delete_user_failure(monkeypatch, async_client):
    from app.api.users import admin as user_admin_module
    from app.crud.auth import user as crud_user
    from app.main import app

    app.dependency_overrides[user_admin_module.get_current_user] = lambda: _admin_user()

    async def fake_get_user_by_id(db, user_id):
        return types.SimpleNamespace(id=user_id)

    async def fake_permanent_delete(db, user_id):
        return False

    monkeypatch.setattr(crud_user, "get_user_by_id", fake_get_user_by_id)
    monkeypatch.setattr(crud_user, "permanently_delete_user", fake_permanent_delete)

    r = await async_client.request(
        "DELETE",
        "/users/00000000-0000-0000-0000-000000000013/permanent",
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert r.status_code == 500


@pytest.mark.asyncio
async def test_search_deleted_users_filters_and_pagination_next(
    monkeypatch, async_client
):
    from app.api.users import admin as user_admin_module
    from app.main import app

    app.dependency_overrides[user_admin_module.get_current_user] = lambda: _admin_user()

    # Only date_created provided to exercise created_at fallback
    def _deleted_user_only_date(idx: int):
        created = "2025-01-01T00:00:00Z"
        return types.SimpleNamespace(
            id=uuid.UUID(f"00000000-0000-0000-0000-{idx:012x}"),
            email=f"u{idx}@example.com",
            username=f"user{idx}",
            is_superuser=False,
            is_verified=False,
            date_created=created,
            oauth_provider=None,
            is_deleted=True,
            deleted_at="2025-01-02T00:00:00Z",
            deleted_by=_admin_user().id,
            deletion_reason="cleanup",
        )

    async def fake_get_deleted_users(db, skip, limit):
        return [_deleted_user_only_date(1), _deleted_user_only_date(2)]

    async def fake_count_deleted_users(db):
        return 4

    monkeypatch.setattr(
        user_admin_module.admin_user_crud, "get_deleted_users", fake_get_deleted_users
    )
    monkeypatch.setattr(
        user_admin_module.admin_user_crud,
        "count_deleted_users",
        fake_count_deleted_users,
    )

    # Page 1 of size 2, total 4 -> has_next True, has_prev False
    r = await async_client.get(
        "/users/deleted/search?deletion_reason=cleanup&deleted_by=00000000-0000-0000-0000-0000000000aa&deleted_after=2025-01-01T00:00:00Z&deleted_before=2025-01-03T00:00:00Z&page=1&size=2",
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert r.status_code == 200
    body = r.json()
    assert body["has_next"] is True
    assert body["has_prev"] is False
    assert set(body["filters_applied"]) == {
        "deletion_reason_search",
        "deleted_by",
        "deletion_date_range",
    }


@pytest.mark.asyncio
async def test_search_deleted_users_pagination_prev_only(monkeypatch, async_client):
    from app.api.users import admin as user_admin_module
    from app.main import app

    app.dependency_overrides[user_admin_module.get_current_user] = lambda: _admin_user()

    async def fake_get_deleted_users(db, skip, limit):
        return [
            types.SimpleNamespace(
                id=uuid.UUID("00000000-0000-0000-0000-0000000000ff"),
                email="u@example.com",
                username="userx",
                is_superuser=False,
                is_verified=False,
                created_at="2025-01-01T00:00:00Z",
                oauth_provider=None,
                is_deleted=True,
                deleted_at="2025-01-02T00:00:00Z",
                deleted_by=_admin_user().id,
                deletion_reason="cleanup",
            )
        ]

    async def fake_count_deleted_users(db):
        return 3

    monkeypatch.setattr(
        user_admin_module.admin_user_crud, "get_deleted_users", fake_get_deleted_users
    )
    monkeypatch.setattr(
        user_admin_module.admin_user_crud,
        "count_deleted_users",
        fake_count_deleted_users,
    )

    # Page 2 of size 2, total 3 -> total_pages 2, has_prev True, has_next False
    r = await async_client.get(
        "/users/deleted/search?page=2&size=2",
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert r.status_code == 200
    body = r.json()
    assert body["has_next"] is False
    assert body["has_prev"] is True
