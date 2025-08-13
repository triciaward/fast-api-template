import uuid

import pytest

from app.schemas.auth.user import APIKeyUser

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_sensitive_health_endpoints_require_api_key(async_client):
    # No Authorization header → 401
    for path in [
        "/api/system/health/detailed",
        "/api/system/health/database",
        "/api/system/health/metrics",
        "/api/system/health/test-sentry",
    ]:
        r = await async_client.get(path)
        assert r.status_code == 401


@pytest.mark.asyncio
async def test_sensitive_health_endpoints_forbidden_without_scope(
    async_client,
    monkeypatch,
):
    # Monkeypatch API key auth to return a user without required scope
    from app.api.users import auth as auth_mod
    from app.main import app

    async def fake_get_api_key_user():  # type: ignore[no-untyped-def]
        return APIKeyUser(
            id=uuid.uuid4(),
            scopes=["other:scope"],
            user_id=None,
            key_id=uuid.uuid4(),
        )

    app.dependency_overrides[auth_mod.get_api_key_user] = fake_get_api_key_user

    for path in [
        "/api/system/health/detailed",
        "/api/system/health/database",
        "/api/system/health/metrics",
    ]:
        r = await async_client.get(path, headers={"Authorization": "Bearer dummy"})
        assert r.status_code == 403
    app.dependency_overrides.pop(auth_mod.get_api_key_user, None)


@pytest.mark.asyncio
async def test_sensitive_health_endpoints_allow_with_scope(async_client, monkeypatch):
    from app.api.users import auth as auth_mod
    from app.main import app

    async def fake_get_api_key_user():  # type: ignore[no-untyped-def]
        return APIKeyUser(
            id=uuid.uuid4(),
            scopes=["system:read"],
            user_id=None,
            key_id=uuid.uuid4(),
        )

    app.dependency_overrides[auth_mod.get_api_key_user] = fake_get_api_key_user

    # detailed/database/metrics should succeed
    for path in [
        "/api/system/health/detailed",
        "/api/system/health/database",
        "/api/system/health/metrics",
    ]:
        r = await async_client.get(path, headers={"Authorization": "Bearer good"})
        assert r.status_code == 200

    # test-sentry will raise 500 after auth passes
    r = await async_client.get(
        "/api/system/health/test-sentry",
        headers={"Authorization": "Bearer good"},
    )
    assert r.status_code == 500
    app.dependency_overrides.pop(auth_mod.get_api_key_user, None)


@pytest.mark.asyncio
async def test_public_health_endpoints_remain_public(async_client):
    for path in [
        "/api/system/health",
        "/api/system/health/simple",
        "/api/system/health/ready",
        "/api/system/health/live",
    ]:
        r = await async_client.get(path)
        assert r.status_code == 200


@pytest.mark.asyncio
async def test_rotation_old_rejected_new_accepted(async_client, monkeypatch):
    """Simulate rotation: old key immediately rejected, new key accepted."""
    from types import SimpleNamespace

    from app.api.users import auth as auth_mod

    # Patch audit logger to no-op
    from app.services.monitoring import audit as audit_mod

    async def _noop(**kwargs):  # type: ignore[no-untyped-def]
        return None

    monkeypatch.setattr(audit_mod, "log_api_key_usage", _noop)

    async def fake_verify(db, raw_key):  # type: ignore[no-untyped-def]
        if raw_key == "newkey":
            return SimpleNamespace(
                id=uuid.uuid4(),
                user_id=None,
                is_active=True,
                expires_at=None,
                scopes=["system:read"],
                label="rotated",
            )
        # Old key should be invalid after rotation
        return None

    monkeypatch.setattr(auth_mod.crud_api_key, "verify_api_key_in_db", fake_verify)

    # Old key rejected
    r = await async_client.get(
        "/api/system/health/detailed",
        headers={"Authorization": "Bearer oldkey"},
    )
    assert r.status_code == 401

    # New key accepted
    r = await async_client.get(
        "/api/system/health/detailed",
        headers={"Authorization": "Bearer newkey"},
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_deactivation_immediate_rejection(async_client, monkeypatch):
    """Simulate deactivation: key becomes inactive and is immediately rejected."""
    from types import SimpleNamespace

    from app.api.users import auth as auth_mod

    # Patch audit logger to no-op
    from app.services.monitoring import audit as audit_mod

    async def _noop(**kwargs):  # type: ignore[no-untyped-def]
        return None

    monkeypatch.setattr(audit_mod, "log_api_key_usage", _noop)

    async def fake_verify(db, raw_key):  # type: ignore[no-untyped-def]
        return SimpleNamespace(
            id=uuid.uuid4(),
            user_id=None,
            is_active=False,  # deactivated
            expires_at=None,
            scopes=["system:read"],
            label="deactivated",
        )

    monkeypatch.setattr(auth_mod.crud_api_key, "verify_api_key_in_db", fake_verify)

    r = await async_client.get(
        "/api/system/health/detailed",
        headers={"Authorization": "Bearer any"},
    )
    assert r.status_code == 401
