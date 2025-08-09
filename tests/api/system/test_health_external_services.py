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
async def test_detailed_health_external_services_configured(monkeypatch, async_client):
    from app.core.config import settings

    monkeypatch.setattr(settings, "SMTP_USERNAME", "user")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "pass")
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 2525)

    resp = await async_client.get(
        "/system/health/detailed",
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["checks"]["external_services"]["email"]["status"] == "configured"
    assert data["checks"]["external_services"]["email"]["host"] == "smtp.example.com"


@pytest.mark.asyncio
async def test_detailed_health_external_services_not_configured(
    monkeypatch,
    async_client,
):
    from app.core.config import settings

    monkeypatch.setattr(settings, "SMTP_USERNAME", None)
    monkeypatch.setattr(settings, "SMTP_PASSWORD", None)

    resp = await async_client.get(
        "/system/health/detailed",
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["checks"]["external_services"]["email"]["status"] == "not_configured"
