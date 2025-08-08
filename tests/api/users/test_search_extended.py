import types

import pytest

pytestmark = pytest.mark.unit


def _schema_user(idx: int):
    uid = f"00000000-0000-0000-0000-00000000000{idx}"
    return types.SimpleNamespace(
        id=uid,
        email=f"u{idx}@ex.com",
        username=f"user{idx}",
        is_superuser=bool(idx % 2),
        is_verified=True,
        created_at="2025-01-01T00:00:00Z",
        oauth_provider="google" if idx % 2 else None,
        is_deleted=False,
        deleted_at=None,
        deleted_by=None,
        deletion_reason=None,
    )


@pytest.mark.asyncio
async def test_search_users_filters_all_and_pagination(monkeypatch, async_client):
    from app.api.users import auth as user_auth
    from app.api.users import search as search_module

    # Auth dependency bypass
    def fake_decode(token, key, algorithms):
        return {"sub": "11111111-1111-1111-1111-111111111111"}

    async def fake_get_user_by_id(db, user_id):
        return _schema_user(9)

    monkeypatch.setattr(user_auth.jwt, "decode", fake_decode)
    from app.crud.auth import user as crud_user

    monkeypatch.setattr(crud_user, "get_user_by_id", fake_get_user_by_id)

    # CRUD results
    async def fake_get_users(db, skip, limit, **kwargs):
        return [_schema_user(1), _schema_user(2), _schema_user(3)]

    async def fake_count(db, **kwargs):
        return 8  # total to exercise pagination calcs

    monkeypatch.setattr(search_module.admin_user_crud, "get_users", fake_get_users)
    monkeypatch.setattr(search_module.admin_user_crud, "count", fake_count)

    # Provide all filters to populate filters_applied list and pagination state
    resp = await async_client.get(
        "/users/search?search=abc&is_verified=true&oauth_provider=google&is_superuser=true"
        "&is_deleted=false&date_created_after=2024-01-01T00:00:00Z&date_created_before=2025-01-01T00:00:00Z"
        "&sort_by=email&sort_order=desc&page=2&size=3",
        headers={"authorization": "Bearer dummy", "user-agent": "pytest"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_count"] == 8
    # filters_applied should include all relevant flags
    for key in [
        "text_search",
        "verification_status",
        "oauth_provider",
        "superuser_status",
        "deletion_status",
        "date_range",
    ]:
        assert key in data["filters_applied"]
    # pagination metadata
    assert data["page"] == 2 and data["per_page"] == 3
    assert data["total_pages"] == 3 and data["has_prev"] is True and data["has_next"] is True
    assert data["sort_field"] == "email" and data["sort_order"] == "desc"


@pytest.mark.asyncio
async def test_list_users_empty(monkeypatch, async_client):
    from app.api.users import auth as user_auth
    from app.api.users import search as search_module

    def fake_decode(token, key, algorithms):
        return {"sub": "11111111-1111-1111-1111-111111111111"}

    async def fake_get_user_by_id(db, user_id):
        return _schema_user(9)

    monkeypatch.setattr(user_auth.jwt, "decode", fake_decode)
    from app.crud.auth import user as crud_user

    monkeypatch.setattr(crud_user, "get_user_by_id", fake_get_user_by_id)

    async def fake_get_users(db, skip, limit, **kwargs):
        return []

    async def fake_count(db, **kwargs):
        return 0

    monkeypatch.setattr(search_module.admin_user_crud, "get_users", fake_get_users)
    monkeypatch.setattr(search_module.admin_user_crud, "count", fake_count)

    resp = await async_client.get(
        "/users/",
        headers={"authorization": "Bearer dummy", "user-agent": "pytest"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["metadata"]["total"] == 0
    assert data["items"] == []


