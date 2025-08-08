"""OAuth authentication tests."""

import types

import pytest
from fastapi import HTTPException

from tests.utils.auth_helpers import (
    MockOAuthService,
    create_test_user,
)

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_oauth_google_success(monkeypatch, async_client):
    """Test successful Google OAuth login."""
    from app.api.auth import login as mod

    class FakeOAuth:
        def is_provider_configured(self, p):
            return True

        async def verify_google_token(self, token):
            return {"sub": "google_123", "email": "user@gmail.com"}

    async def fake_get_user_by_oauth_id(db, provider, oid):
        return create_test_user(oauth_provider="google", oauth_id="google_123")

    async def fake_create_user_session(db, user, request):
        return "access_token", "refresh_token"

    def fake_set_refresh_token_cookie(response, token):
        pass

    monkeypatch.setattr(mod, "oauth_service", FakeOAuth())
    monkeypatch.setattr(
        mod.crud_user, "get_user_by_oauth_id", fake_get_user_by_oauth_id,
    )

    from app.services.auth import refresh_token as rt

    monkeypatch.setattr(rt, "create_user_session", fake_create_user_session)
    monkeypatch.setattr(rt, "set_refresh_token_cookie", fake_set_refresh_token_cookie)

    resp = await async_client.post(
        "/auth/oauth/login",
        json={"provider": "google", "access_token": "valid_token"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"] == "access_token"
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_oauth_apple_success(monkeypatch, async_client):
    """Test successful Apple OAuth login."""
    from app.api.auth import login as mod

    class FakeOAuth:
        def is_provider_configured(self, p):
            return True

        async def verify_apple_token(self, token):
            return {"sub": "apple_123", "email": "user@icloud.com"}

    async def fake_get_user_by_oauth_id(db, provider, oid):
        return create_test_user(oauth_provider="apple", oauth_id="apple_123")

    async def fake_create_user_session(db, user, request):
        return "access_token", "refresh_token"

    def fake_set_refresh_token_cookie(response, token):
        pass

    monkeypatch.setattr(mod, "oauth_service", FakeOAuth())
    monkeypatch.setattr(
        mod.crud_user, "get_user_by_oauth_id", fake_get_user_by_oauth_id,
    )

    from app.services.auth import refresh_token as rt

    monkeypatch.setattr(rt, "create_user_session", fake_create_user_session)
    monkeypatch.setattr(rt, "set_refresh_token_cookie", fake_set_refresh_token_cookie)

    resp = await async_client.post(
        "/auth/oauth/login",
        json={"provider": "apple", "access_token": "valid_token"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"] == "access_token"
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_oauth_provider_not_configured(monkeypatch, async_client):
    """Test OAuth with unconfigured provider returns 400."""
    from app.api.auth import login as mod

    class FakeOAuth:
        def is_provider_configured(self, p):
            return False

    monkeypatch.setattr(mod, "oauth_service", FakeOAuth())

    resp = await async_client.post(
        "/auth/oauth/login",
        json={"provider": "google", "access_token": "token"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 400
    assert "not configured" in resp.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_oauth_service_unavailable(monkeypatch):
    """Test OAuth when service is completely unavailable."""
    from app.api.auth import login as mod

    monkeypatch.setattr(mod, "oauth_service", None)
    req = types.SimpleNamespace(headers={})
    resp = types.SimpleNamespace()
    data = types.SimpleNamespace(provider="google", access_token="t")

    with pytest.raises(HTTPException) as ex:
        await mod.oauth_login(req, resp, data, db=object())
    assert ex.value.status_code == 503


@pytest.mark.asyncio
async def test_oauth_invalid_apple_token(monkeypatch):
    """Test OAuth with invalid Apple token."""
    from app.api.auth import login as mod

    class FakeOAuth:
        def is_provider_configured(self, p):
            return True

        async def verify_apple_token(self, token):
            return None

    monkeypatch.setattr(mod, "oauth_service", FakeOAuth())
    req = types.SimpleNamespace(headers={})
    resp = types.SimpleNamespace()
    data = types.SimpleNamespace(provider="apple", access_token="invalid")

    with pytest.raises(HTTPException) as ex:
        await mod.oauth_login(req, resp, data, db=object())
    assert ex.value.status_code == 400


@pytest.mark.asyncio
async def test_oauth_invalid_user_info(monkeypatch):
    """Test OAuth with invalid user info from provider."""
    from app.api.auth import login as mod

    class FakeOAuth:
        def is_provider_configured(self, p):
            return True

        async def verify_google_token(self, token):
            return {"sub": None, "email": None}

    monkeypatch.setattr(mod, "oauth_service", FakeOAuth())
    req = types.SimpleNamespace(headers={})
    resp = types.SimpleNamespace()
    data = types.SimpleNamespace(provider="google", access_token="token")

    with pytest.raises(HTTPException) as ex:
        await mod.oauth_login(req, resp, data, db=object())
    assert ex.value.status_code == 400


@pytest.mark.asyncio
async def test_oauth_unsupported_provider_direct(monkeypatch):
    """Test OAuth with unsupported provider."""
    from app.api.auth import login as mod

    monkeypatch.setattr(mod, "oauth_service", MockOAuthService(configured_providers=[]))
    req = types.SimpleNamespace(headers={})
    resp = types.SimpleNamespace()
    data = types.SimpleNamespace(provider="unknown", access_token="token")

    with pytest.raises(HTTPException) as ex:
        await mod.oauth_login(req, resp, data, db=object())
    assert ex.value.status_code == 400


@pytest.mark.asyncio
async def test_oauth_unexpected_exception_in_session(monkeypatch):
    """Test OAuth handles session creation failures."""
    from app.api.auth import login as mod

    class FakeOAuth:
        def is_provider_configured(self, p):
            return True

        async def verify_google_token(self, token):
            return {"sub": "gidX", "email": "x@example.com"}

    async def fake_get_user_by_oauth_id(db, provider, oid):
        return types.SimpleNamespace(id="11111111-1111-1111-1111-111111111111")

    async def boom(*a, **k):
        raise RuntimeError("session creation failed")

    monkeypatch.setattr(mod, "oauth_service", FakeOAuth())
    monkeypatch.setattr(
        mod.crud_user, "get_user_by_oauth_id", fake_get_user_by_oauth_id,
    )

    from app.services.auth import refresh_token as svc

    monkeypatch.setattr(svc, "create_user_session", boom)

    req = types.SimpleNamespace(headers={})
    resp = types.SimpleNamespace()
    data = types.SimpleNamespace(provider="google", access_token="token")

    with pytest.raises(HTTPException) as ex:
        await mod.oauth_login(req, resp, data, db=object())
    assert ex.value.status_code == 400


def test_get_oauth_providers_none_configured(monkeypatch):
    """Test getting OAuth providers when none are configured."""
    from app.api.auth import login as mod

    monkeypatch.setattr(mod, "oauth_service", None)

    import anyio

    async def run():
        assert await mod.get_oauth_providers() == {"providers": []}

    anyio.run(run)


def test_get_oauth_providers_some_configured(monkeypatch):
    """Test getting OAuth providers when some are configured."""
    from app.api.auth import login as mod

    class BothConfigured:
        def is_provider_configured(self, p):
            return p in ["google", "apple"]

    monkeypatch.setattr(mod, "oauth_service", BothConfigured())

    import anyio

    async def run():
        assert await mod.get_oauth_providers() == {"providers": ["google", "apple"]}

    anyio.run(run)


def test_get_oauth_providers_partial_configuration(monkeypatch):
    """Test getting OAuth providers with partial configurations."""
    from app.api.auth import login as mod

    class OnlyGoogle:
        def is_provider_configured(self, p):
            return p == "google"

    class OnlyApple:
        def is_provider_configured(self, p):
            return p == "apple"

    class NoneConfigured:
        def is_provider_configured(self, p):
            return False

    import anyio

    async def run_cases():
        # Only Google configured
        monkeypatch.setattr(mod, "oauth_service", OnlyGoogle())
        assert await mod.get_oauth_providers() == {"providers": ["google"]}

        # Only Apple configured
        monkeypatch.setattr(mod, "oauth_service", OnlyApple())
        assert await mod.get_oauth_providers() == {"providers": ["apple"]}

        # None configured
        monkeypatch.setattr(mod, "oauth_service", NoneConfigured())
        assert await mod.get_oauth_providers() == {"providers": []}

    anyio.run(run_cases)
