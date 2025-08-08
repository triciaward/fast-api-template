import sys
import types

import pytest


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
