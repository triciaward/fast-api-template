import pytest


@pytest.mark.asyncio
async def test_detailed_health_external_services_configured(monkeypatch, async_client):
    from app.core.config import settings

    monkeypatch.setattr(settings, "SMTP_USERNAME", "user")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "pass")
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 2525)

    resp = await async_client.get("/system/health/detailed", headers={"user-agent": "pytest"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["checks"]["external_services"]["email"]["status"] == "configured"
    assert data["checks"]["external_services"]["email"]["host"] == "smtp.example.com"


@pytest.mark.asyncio
async def test_detailed_health_external_services_not_configured(monkeypatch, async_client):
    from app.core.config import settings

    monkeypatch.setattr(settings, "SMTP_USERNAME", None)
    monkeypatch.setattr(settings, "SMTP_PASSWORD", None)

    resp = await async_client.get("/system/health/detailed", headers={"user-agent": "pytest"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["checks"]["external_services"]["email"]["status"] == "not_configured"

