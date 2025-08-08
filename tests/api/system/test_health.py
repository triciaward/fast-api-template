import pytest

pytestmark = pytest.mark.template_only


@pytest.mark.asyncio
async def test_root_endpoint(async_client):
    resp = await async_client.get("/")
    assert resp.status_code == 200
    assert "message" in resp.json()


@pytest.mark.asyncio
async def test_simple_health(async_client):
    resp = await async_client.get("/system/health/simple")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_liveness(async_client):
    resp = await async_client.get("/system/health/live")
    assert resp.status_code == 200
    data = resp.json()
    assert data["alive"] == "true"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_metrics(async_client):
    resp = await async_client.get("/system/health/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "system" in data and "application" in data


@pytest.mark.asyncio
async def test_rate_limit_info(async_client):
    resp = await async_client.get("/system/health/rate-limit")
    assert resp.status_code == 200
    data = resp.json()
    assert "enabled" in data and "configuration" in data
