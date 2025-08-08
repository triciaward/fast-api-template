"""Login error scenarios and exception handling tests."""

import types

import pytest
from fastapi import HTTPException

from tests.utils.auth_helpers import (
    mock_authentication_failure,
)

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_login_unexpected_error_returns_500(monkeypatch, async_client):
    """Test unexpected database errors during login return 500."""
    mock_authentication_failure(monkeypatch, reason="exception")

    resp = await async_client.post(
        "/auth/login",
        data={"username": "user@example.com", "password": "secret"},
        headers={
            "content-type": "application/x-www-form-urlencoded",
            "user-agent": "pytest",
        },
    )
    assert resp.status_code == 500
    assert "Login failed" in resp.json().get("detail", "") or resp.json().get("error")


@pytest.mark.asyncio
async def test_login_unexpected_error_maps_to_500_with_validation_bypass(
    monkeypatch, async_client
):
    """Test login error handling with email validation bypassed."""
    from app.api.auth import login as mod

    async def boom(*args, **kwargs):
        raise Exception("db failure")

    # Patch validators to pass email format
    import app.core.security.validation as validation

    monkeypatch.setattr(validation, "validate_email_format", lambda e: (True, ""))
    monkeypatch.setattr(mod.crud_user, "authenticate_user", boom)

    # Avoid audit DB writes
    from app.services.monitoring import audit

    async def noop(*args, **kwargs):
        return None

    monkeypatch.setattr(audit, "log_login_attempt", noop)

    resp = await async_client.post(
        "/auth/login",
        data={"username": "a@example.com", "password": "Passw0rd!"},
        headers={
            "content-type": "application/x-www-form-urlencoded",
            "user-agent": "pytest",
        },
    )
    assert resp.status_code == 500
    assert "login failed" in resp.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_register_general_exception_handling(monkeypatch):
    """Test registration handles general exceptions properly."""
    from app.api.auth import login as mod

    # Call function directly to bypass FastAPI validation and inject fake db
    async def mk_user(*a, **k):
        raise RuntimeError("boom")

    user = types.SimpleNamespace(
        email="e@example.com", username="zetatest", password="Passw0rd!"
    )

    monkeypatch.setattr(mod.crud_user, "get_user_by_email", lambda *a, **k: None)
    monkeypatch.setattr(mod.crud_user, "get_user_by_username", lambda *a, **k: None)
    monkeypatch.setattr(mod.crud_user, "create_user", mk_user)

    with pytest.raises(HTTPException) as ex:
        await mod.register_user(user, db=object())
    assert ex.value.status_code == 500


@pytest.mark.asyncio
async def test_register_verification_token_none_still_succeeds(
    monkeypatch, async_client
):
    """Test registration succeeds even if verification token creation fails."""
    from app.api.auth import login as mod

    async def none(*a, **k):
        return None

    async def mk_user(db, user):
        return types.SimpleNamespace(
            id="11111111-1111-1111-1111-111111111111",
            email=user.email,
            username=user.username,
            is_superuser=False,
            is_verified=False,
            created_at="2024-01-01T00:00:00Z",
            is_deleted=False,
        )

    class FakeEmail:
        def is_configured(self):
            return True

        async def create_verification_token(self, db, uid):
            return None  # Token creation fails

        def send_verification_email(self, *a, **k):
            return None

    monkeypatch.setattr(mod.crud_user, "get_user_by_email", none)
    monkeypatch.setattr(mod.crud_user, "get_user_by_username", none)
    monkeypatch.setattr(mod.crud_user, "create_user", mk_user)
    monkeypatch.setattr(mod, "email_service", FakeEmail())

    resp = await async_client.post(
        "/auth/register",
        json={
            "email": "e@example.com",
            "username": "zetatest",
            "password": "Passw0rd!",
        },
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 201
