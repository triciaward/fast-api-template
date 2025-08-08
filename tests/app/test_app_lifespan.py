import pytest


@pytest.mark.asyncio
async def test_app_starts_with_rate_limiting_and_redis(monkeypatch, async_client):
    # Enable flags; init functions in services are no-ops by design in template
    from app.core.config import config as cfg

    monkeypatch.setattr(cfg.settings, "ENABLE_RATE_LIMITING", True, raising=False)
    monkeypatch.setattr(cfg.settings, "ENABLE_REDIS", True, raising=False)

    # Call a simple endpoint to ensure app initialized without errors
    r = await async_client.get("/")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_features_endpoint_reflects_flags(monkeypatch, async_client):
    from app.core.config import config as cfg

    monkeypatch.setattr(cfg.settings, "ENABLE_REDIS", False, raising=False)
    monkeypatch.setattr(cfg.settings, "ENABLE_WEBSOCKETS", True, raising=False)
    monkeypatch.setattr(cfg.settings, "ENABLE_RATE_LIMITING", False, raising=False)
    monkeypatch.setattr(cfg.settings, "ENABLE_CELERY", True, raising=False)

    r = await async_client.get("/features")
    assert r.status_code == 200
    data = r.json()
    assert data == {
        "redis": False,
        "websockets": True,
        "rate_limiting": False,
        "celery": True,
    }
