import types
import uuid

import pytest

pytestmark = pytest.mark.unit


def _admin():
    return types.SimpleNamespace(id=uuid.UUID("00000000-0000-0000-0000-0000000000aa"))


@pytest.mark.asyncio
async def test_list_users_with_filters(monkeypatch, async_client):
    from app.api.admin import users as mod
    from app.main import app

    app.dependency_overrides[mod.require_superuser] = lambda: _admin()

    async def fake_get_users(
        db,
        skip,
        limit,
        is_superuser,
        is_verified,
        is_deleted,
        oauth_provider,
    ):
        return [
            types.SimpleNamespace(
                id=uuid.uuid4(),
                email="a@example.com",
                username="axxx",
                is_superuser=False,
                is_verified=True,
                is_deleted=False,
                created_at="2025-01-01T00:00:00Z",
                oauth_provider=None,
                oauth_id=None,
                oauth_email=None,
                deletion_requested_at=None,
                deletion_confirmed_at=None,
                deletion_scheduled_for=None,
            ),
        ]

    async def fake_count(db, filters):
        # Ensure filters propagated
        assert filters["is_verified"] is True and filters["is_deleted"] is False
        return 1

    monkeypatch.setattr(mod.admin_user_crud, "get_users", fake_get_users)
    monkeypatch.setattr(mod.admin_user_crud, "count", fake_count)

    r = await async_client.get("/admin/users?is_verified=true&is_deleted=false")
    app.dependency_overrides.clear()
    assert r.status_code == 200
    assert r.json()["metadata"]["total"] == 1


@pytest.mark.asyncio
async def test_get_user_not_found(monkeypatch, async_client):
    from app.api.admin import users as mod
    from app.main import app

    app.dependency_overrides[mod.require_superuser] = lambda: _admin()

    async def fake_get(db, uid):
        return None

    monkeypatch.setattr(mod.admin_user_crud, "get", fake_get)

    r = await async_client.get(f"/admin/users/{uuid.uuid4()}")
    app.dependency_overrides.clear()
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_create_user_conflicts_and_failure(monkeypatch, async_client):
    from app.api.admin import users as mod
    from app.main import app

    app.dependency_overrides[mod.require_superuser] = lambda: _admin()

    # Email conflict
    async def email_conflict(db, e):
        return object()

    monkeypatch.setattr(mod.admin_user_crud, "get_user_by_email", email_conflict)
    r = await async_client.post(
        "/admin/users",
        json={
            "email": "x@example.com",
            "username": "userxxx",
            "password": "Password123!",
            "is_superuser": False,
        },
    )
    assert r.status_code == 400

    # Username conflict
    async def none_email(db, e):
        return None

    async def username_conflict(db, u):
        return object()

    monkeypatch.setattr(mod.admin_user_crud, "get_user_by_email", none_email)
    monkeypatch.setattr(mod.admin_user_crud, "get_user_by_username", username_conflict)
    r = await async_client.post(
        "/admin/users",
        json={
            "email": "x2@example.com",
            "username": "useryyy",
            "password": "Password123!",
            "is_superuser": False,
        },
    )
    assert r.status_code == 400

    # Create failure
    async def username_ok(db, u):
        return None

    async def create_fail(db, uc):
        return None

    monkeypatch.setattr(mod.admin_user_crud, "get_user_by_username", username_ok)
    monkeypatch.setattr(mod.admin_user_crud, "create_user", create_fail)
    r = await async_client.post(
        "/admin/users",
        json={
            "email": "x3@example.com",
            "username": "userzzz",
            "password": "Password123!",
            "is_superuser": False,
        },
    )
    app.dependency_overrides.clear()
    assert r.status_code == 500


@pytest.mark.asyncio
async def test_update_user_conflicts_not_found_and_failure(monkeypatch, async_client):
    from app.api.admin import users as mod
    from app.main import app

    app.dependency_overrides[mod.require_superuser] = lambda: _admin()

    uid = uuid.uuid4()

    # Not found
    async def get_none(db, u):
        return None

    monkeypatch.setattr(mod.admin_user_crud, "get", get_none)
    r = await async_client.put(f"/admin/users/{uid}", json={})
    assert r.status_code == 404

    # Found but email conflict
    existing = types.SimpleNamespace(id=uid, email="e@x", username="u")

    async def get_existing(db, u):
        return existing

    monkeypatch.setattr(mod.admin_user_crud, "get", get_existing)

    async def email_conflict2(db, e):
        return object()

    monkeypatch.setattr(mod.admin_user_crud, "get_user_by_email", email_conflict2)
    r = await async_client.put(f"/admin/users/{uid}", json={"email": "new@example.com"})
    assert r.status_code == 400

    # Username conflict
    async def none_email2(db, e):
        return None

    async def username_conflict2(db, u):
        return object()

    monkeypatch.setattr(mod.admin_user_crud, "get_user_by_email", none_email2)
    monkeypatch.setattr(mod.admin_user_crud, "get_user_by_username", username_conflict2)
    r = await async_client.put(f"/admin/users/{uid}", json={"username": "userabc"})
    assert r.status_code == 400

    # Update failure
    async def username_ok2(db, u):
        return None

    async def update_fail(db, u, d):
        return None

    monkeypatch.setattr(mod.admin_user_crud, "get_user_by_username", username_ok2)
    monkeypatch.setattr(mod.admin_user_crud, "update_user", update_fail)
    r = await async_client.put(f"/admin/users/{uid}", json={"username": "userabc"})
    app.dependency_overrides.clear()
    assert r.status_code == 500


@pytest.mark.asyncio
async def test_delete_user_self_not_found_and_failure(monkeypatch, async_client):
    from app.api.admin import users as mod
    from app.main import app

    admin = _admin()
    app.dependency_overrides[mod.require_superuser] = lambda: admin

    # Self-delete
    r = await async_client.delete(f"/admin/users/{admin.id}")
    assert r.status_code == 400

    # Not found
    async def get_none2(db, u):
        return None

    monkeypatch.setattr(mod.admin_user_crud, "get", get_none2)
    r = await async_client.delete(f"/admin/users/{uuid.uuid4()}")
    assert r.status_code == 404

    # Failure
    async def get_ok(db, u):
        return object()

    async def delete_fail(db, u):
        return False

    monkeypatch.setattr(mod.admin_user_crud, "get", get_ok)
    monkeypatch.setattr(mod.admin_user_crud, "delete_user", delete_fail)
    r = await async_client.delete(f"/admin/users/{uuid.uuid4()}")
    app.dependency_overrides.clear()
    assert r.status_code == 500


@pytest.mark.asyncio
async def test_toggle_superuser_self_and_not_found(monkeypatch, async_client):
    from app.api.admin import users as mod
    from app.main import app

    admin = _admin()
    app.dependency_overrides[mod.require_superuser] = lambda: admin

    # Self
    r = await async_client.post(f"/admin/users/{admin.id}/toggle-superuser")
    assert r.status_code == 400

    # Not found
    async def toggle_none(db, u):
        return None

    monkeypatch.setattr(mod.admin_user_crud, "toggle_superuser_status", toggle_none)
    r = await async_client.post(f"/admin/users/{uuid.uuid4()}/toggle-superuser")
    app.dependency_overrides.clear()
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_toggle_verification_not_found(monkeypatch, async_client):
    from app.api.admin import users as mod
    from app.main import app

    app.dependency_overrides[mod.require_superuser] = lambda: _admin()

    async def toggle_none(db, u):
        return None

    monkeypatch.setattr(mod.admin_user_crud, "toggle_verification_status", toggle_none)

    r = await async_client.post(f"/admin/users/{uuid.uuid4()}/toggle-verification")
    app.dependency_overrides.clear()
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_force_delete_not_found_and_failure(monkeypatch, async_client):
    from app.api.admin import users as mod
    from app.main import app

    app.dependency_overrides[mod.require_superuser] = lambda: _admin()

    async def get_none3(db, u):
        return None

    monkeypatch.setattr(mod.admin_user_crud, "get", get_none3)
    r = await async_client.post(f"/admin/users/{uuid.uuid4()}/force-delete")
    assert r.status_code == 404

    async def get_ok2(db, u):
        return object()

    async def force_fail(db, u):
        return False

    monkeypatch.setattr(mod.admin_user_crud, "get", get_ok2)
    monkeypatch.setattr(mod.admin_user_crud, "force_delete_user", force_fail)
    r = await async_client.post(f"/admin/users/{uuid.uuid4()}/force-delete")
    app.dependency_overrides.clear()
    assert r.status_code == 500


@pytest.mark.asyncio
async def test_bulk_operations_variants(monkeypatch, async_client):
    from app.api.admin import users as mod
    from app.main import app

    app.dependency_overrides[mod.require_superuser] = lambda: _admin()

    uid = uuid.uuid4()

    # verify path where user becomes verified on second toggle
    calls = {"n": 0}

    async def toggle_ver(db, u):
        calls["n"] += 1
        return types.SimpleNamespace(is_verified=(calls["n"] % 2 == 0))

    monkeypatch.setattr(mod.admin_user_crud, "toggle_verification_status", toggle_ver)

    r = await async_client.post(
        "/admin/bulk-operations",
        json={"operation": "verify", "user_ids": [str(uid)]},
    )
    assert r.status_code == 200 and r.json()["successful"] == 1

    # unverify path where user becomes unverified on second toggle
    calls = {"n": 0}

    async def toggle_ver2(db, u):
        calls["n"] += 1
        return types.SimpleNamespace(is_verified=(calls["n"] % 2 == 1))

    monkeypatch.setattr(mod.admin_user_crud, "toggle_verification_status", toggle_ver2)

    r = await async_client.post(
        "/admin/bulk-operations",
        json={"operation": "unverify", "user_ids": [str(uid)]},
    )
    assert r.status_code == 200 and r.json()["successful"] == 1

    # exception path using a valid operation
    async def toggle_raise(*a, **k):
        raise RuntimeError("x")

    monkeypatch.setattr(mod.admin_user_crud, "toggle_verification_status", toggle_raise)
    r = await async_client.post(
        "/admin/bulk-operations",
        json={"operation": "verify", "user_ids": [str(uid)]},
    )
    app.dependency_overrides.clear()
    assert r.status_code == 200
    body = r.json()
    assert body["failed"] == 1 and body["successful"] == 0
