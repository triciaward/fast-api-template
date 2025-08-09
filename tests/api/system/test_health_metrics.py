import sys
import types

import pytest


@pytest.fixture(autouse=True)
async def _override_health_api_key_dependency():
    from uuid import uuid4

    from app.api.users import auth as auth_mod
    from app.main import app
    from app.schemas.auth.user import APIKeyUser

    async def fake_get_api_key_user():  # type: ignore[no-untyped-def]
        return APIKeyUser(
            id=uuid4(),
            scopes=["system:read"],
            user_id=None,
            key_id=uuid4(),
        )

    app.dependency_overrides[auth_mod.get_api_key_user] = fake_get_api_key_user
    try:
        yield
    finally:
        app.dependency_overrides.pop(auth_mod.get_api_key_user, None)


@pytest.mark.asyncio
async def test_metrics_endpoint(monkeypatch, async_client):
    from app.core.config import settings

    # Patch psutil to stable values
    ps = types.SimpleNamespace(
        cpu_percent=lambda interval=1: 5.0,
        virtual_memory=lambda: types.SimpleNamespace(percent=42.0, available=123456789),
        disk_usage=lambda path: types.SimpleNamespace(percent=11.0, free=987654321),
    )

    # Ensure our fake psutil is used when the endpoint imports it
    monkeypatch.setitem(sys.modules, "psutil", ps)

    r = await async_client.get("/system/health/metrics")
    assert r.status_code == 200
    data = r.json()
    assert "system" in data and "application" in data
    assert data["system"]["cpu_percent"] == 5.0
    assert data["application"]["features"]["redis_enabled"] == settings.ENABLE_REDIS
