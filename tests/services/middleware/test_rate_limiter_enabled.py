import pytest


@pytest.mark.asyncio
async def test_rate_limit_info_when_enabled(monkeypatch, async_client):
    from app.core.config import settings

    monkeypatch.setattr(settings, "ENABLE_RATE_LIMITING", True)

    resp = await async_client.get(
        "/system/health/rate-limit",
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["enabled"] is True
    assert "configuration" in data
