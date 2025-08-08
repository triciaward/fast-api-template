import types

import pytest

pytestmark = pytest.mark.unit


def _schema_user(idx: int):
    # Minimal object with attributes accessed by search endpoints
    uuid = f"00000000-0000-0000-0000-00000000000{idx}"
    return types.SimpleNamespace(
        id=uuid,
        email=f"u{idx}@example.com",
        username=f"user{idx}",
        is_superuser=False,
        is_verified=True,
        created_at="2025-01-01T00:00:00Z",
        oauth_provider=None,
        is_deleted=False,
        deleted_at=None,
        deleted_by=None,
        deletion_reason=None,
    )


@pytest.mark.asyncio
async def test_list_users_basic(monkeypatch, async_client):
    from app.api.users import search as search_module

    async def fake_get_users(db, skip, limit, **kwargs):
        return [_schema_user(1), _schema_user(2)]

    async def fake_count(db, **kwargs):
        return 2

    # Bypass auth dependency get_current_user
    from app.api.users import auth as user_auth

    def fake_decode(token, key, algorithms):
        return {"sub": "11111111-1111-1111-1111-111111111111"}

    async def fake_get_user_by_id(db, user_id):
        return _schema_user(9)

    monkeypatch.setattr(user_auth.jwt, "decode", fake_decode)
    from app.crud.auth import user as crud_user

    monkeypatch.setattr(crud_user, "get_user_by_id", fake_get_user_by_id)

    monkeypatch.setattr(search_module.admin_user_crud, "get_users", fake_get_users)
    monkeypatch.setattr(search_module.admin_user_crud, "count", fake_count)

    resp = await async_client.get(
        "/users/",
        headers={"authorization": "Bearer dummy", "user-agent": "pytest"},
    )
    assert resp.status_code == 200
    data = resp.json()
    # PaginatedResponse shape: { items: [...], metadata: { page, size, total, ... } }
    assert data["metadata"]["page"] == 1 and data["metadata"]["size"] >= 1
    assert data["metadata"]["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_search_users_metadata(monkeypatch, async_client):
    from app.api.users import search as search_module

    async def fake_get_users(db, skip, limit, **kwargs):
        return [_schema_user(3)]

    async def fake_count(db, **kwargs):
        return 1

    from app.api.users import auth as user_auth

    def fake_decode(token, key, algorithms):
        return {"sub": "11111111-1111-1111-1111-111111111111"}

    async def fake_get_user_by_id(db, user_id):
        return _schema_user(9)

    monkeypatch.setattr(user_auth.jwt, "decode", fake_decode)
    from app.crud.auth import user as crud_user

    monkeypatch.setattr(crud_user, "get_user_by_id", fake_get_user_by_id)

    monkeypatch.setattr(search_module.admin_user_crud, "get_users", fake_get_users)
    monkeypatch.setattr(search_module.admin_user_crud, "count", fake_count)

    resp = await async_client.get(
        "/users/search?search=abc&is_verified=true&sort_by=username&sort_order=asc",
        headers={"authorization": "Bearer dummy", "user-agent": "pytest"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_count"] == 1
    assert data["search_applied"] is True
    assert "verification_status" in data["filters_applied"]
    assert data["sort_field"] == "username"
    assert data["sort_order"] == "asc"
