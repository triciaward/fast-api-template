"""Login input validation and error handling tests."""

import types

import pytest

from tests.utils.auth_helpers import (
    MockEmailService,
    mock_authentication_failure,
)

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_login_invalid_email_format(async_client):
    """Test login with invalid email format returns 400."""
    resp = await async_client.post(
        "/api/auth/login",
        data={"username": "not-an-email", "password": "x"},
        headers={
            "content-type": "application/x-www-form-urlencoded",
            "user-agent": "pytest",
        },
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login_invalid_credentials(monkeypatch, async_client):
    """Test login with invalid credentials returns 401."""
    mock_authentication_failure(monkeypatch, reason="invalid_credentials")

    resp = await async_client.post(
        "/api/auth/login",
        data={"username": "user@example.com", "password": "wrong"},
        headers={
            "content-type": "application/x-www-form-urlencoded",
            "user-agent": "pytest",
        },
    )
    assert resp.status_code == 401
    body = resp.json()
    assert "Invalid email or password" in body.get("detail", "") or body.get("error")


@pytest.mark.asyncio
async def test_login_unverified_user_blocked(monkeypatch, async_client):
    """Test unverified users are blocked from login."""
    mock_authentication_failure(monkeypatch, reason="unverified")

    resp = await async_client.post(
        "/api/auth/login",
        data={"username": "user@example.com", "password": "secret"},
        headers={
            "content-type": "application/x-www-form-urlencoded",
            "user-agent": "pytest",
        },
    )
    assert resp.status_code == 401
    body = resp.json()
    assert "verify your email" in body.get("detail", "").lower() or body.get("error")


@pytest.mark.asyncio
async def test_login_invalid_password_with_validation(monkeypatch, async_client):
    """Test login with invalid password after email validation passes."""
    import app.core.security as sec
    from app.api.auth import login as mod

    monkeypatch.setattr(sec, "validate_email_format", lambda email: (True, None))

    async def fake_auth(db, email, password):
        return None

    async def fake_log_login_attempt(db, request, user, success):
        return None

    monkeypatch.setattr(mod.crud_user, "authenticate_user", fake_auth)
    monkeypatch.setattr(mod, "log_login_attempt", fake_log_login_attempt)

    resp = await async_client.post(
        "/api/auth/login",
        data={"username": "u@example.com", "password": "bad"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 401
    assert "invalid" in resp.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_register_email_already_exists(monkeypatch, async_client):
    """Test registration with existing email returns 400."""
    from app.api.auth import login as mod

    async def fake_get_user_by_email(db, email):
        return object()  # User exists

    monkeypatch.setattr(mod.crud_user, "get_user_by_email", fake_get_user_by_email)

    resp = await async_client.post(
        "/api/auth/register",
        json={
            "email": "existing@example.com",
            "username": "newuser",
            "password": "Passw0rd!",
        },
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 400
    assert "email already" in resp.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_register_username_already_exists(monkeypatch, async_client):
    """Test registration with existing username returns 400."""
    from app.api.auth import login as mod

    async def fake_get_user_by_email(db, email):
        return None

    async def fake_get_user_by_username(db, username):
        return object()  # Username exists

    monkeypatch.setattr(mod.crud_user, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(
        mod.crud_user,
        "get_user_by_username",
        fake_get_user_by_username,
    )

    resp = await async_client.post(
        "/api/auth/register",
        json={
            "email": "new@example.com",
            "username": "existing",
            "password": "Passw0rd!",
        },
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 400
    assert "username" in resp.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_register_email_service_not_configured_still_succeeds(
    monkeypatch,
    async_client,
):
    """Test registration succeeds even when email service is not configured."""
    from app.api.auth import login as mod

    async def fake_get_user_by_email(db, email):
        return None

    async def fake_get_user_by_username(db, username):
        return None

    async def fake_create_user(db, user):
        return types.SimpleNamespace(
            id="11111111-1111-1111-1111-111111111111",
            email=user.email,
            username=user.username,
            is_superuser=False,
            is_verified=False,
            created_at="2024-01-01T00:00:00Z",
            is_deleted=False,
        )

    monkeypatch.setattr(mod.crud_user, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(
        mod.crud_user,
        "get_user_by_username",
        fake_get_user_by_username,
    )
    monkeypatch.setattr(mod.crud_user, "create_user", fake_create_user)
    monkeypatch.setattr(mod, "email_service", MockEmailService(configured=False))

    resp = await async_client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "Passw0rd!",
        },
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
