import pytest

pytestmark = pytest.mark.template_only


# Autouse override for API key on protected health endpoints in this module
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
async def test_root_endpoint(async_client):
    resp = await async_client.get("/")
    assert resp.status_code == 200
    assert "message" in resp.json()


@pytest.mark.asyncio
async def test_simple_health(async_client):
    resp = await async_client.get("/api/system/health/simple")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_liveness(async_client):
    resp = await async_client.get("/api/system/health/live")
    assert resp.status_code == 200
    data = resp.json()
    assert data["alive"] == "true"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_metrics(async_client):
    resp = await async_client.get("/api/system/health/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "system" in data and "application" in data


@pytest.mark.asyncio
async def test_rate_limit_info(async_client):
    resp = await async_client.get("/api/system/health/rate-limit")
    assert resp.status_code == 200
    data = resp.json()
    assert "enabled" in data and "configuration" in data
