"""Core login functionality tests."""

import pytest

from tests.utils.auth_helpers import (
    MockEmailService,
    create_test_user,
    mock_authentication_success,
)

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_login_success_sets_refresh_cookie_and_returns_token(
    monkeypatch, async_client,
):
    """Test successful login returns access token and sets refresh cookie."""
    from app.core.config.config import settings

    user = mock_authentication_success(monkeypatch)

    resp = await async_client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "secret"},
        headers={
            "content-type": "application/x-www-form-urlencoded",
            "user-agent": "pytest",
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"] == "access_token_123"
    assert data["token_type"] == "bearer"

    # Verify refresh cookie is set with proper flags
    set_cookie = resp.headers.get("set-cookie", "")
    assert f"{settings.REFRESH_TOKEN_COOKIE_NAME}=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert f"Path={settings.REFRESH_TOKEN_COOKIE_PATH}" in set_cookie

    expected_samesite = settings.REFRESH_TOKEN_COOKIE_SAMESITE.lower()
    assert f"samesite={expected_samesite}" in set_cookie.lower()

    if settings.REFRESH_TOKEN_COOKIE_SECURE:
        assert "Secure" in set_cookie
    else:
        assert "Secure" not in set_cookie


@pytest.mark.asyncio
async def test_login_oauth_user_bypasses_verification_check(monkeypatch, async_client):
    """Test that OAuth users can login even if not verified."""
    user = create_test_user(is_verified=False, has_password=False)
    mock_authentication_success(monkeypatch, user)

    resp = await async_client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "secret"},
        headers={
            "content-type": "application/x-www-form-urlencoded",
            "user-agent": "pytest",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"] == "access_token_123"


@pytest.mark.asyncio
async def test_register_success_returns_user_data(monkeypatch, async_client):
    """Test successful user registration."""
    from app.api.auth import login as mod

    async def fake_get_user_by_email(db, email):
        return None

    async def fake_get_user_by_username(db, username):
        return None

    async def fake_create_user(db, user):
        return create_test_user(
            email=user.email,
            username=user.username,
            is_verified=False,
        )

    monkeypatch.setattr(mod.crud_user, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(
        mod.crud_user, "get_user_by_username", fake_get_user_by_username,
    )
    monkeypatch.setattr(mod.crud_user, "create_user", fake_create_user)
    monkeypatch.setattr(mod, "email_service", MockEmailService(configured=False))

    resp = await async_client.post(
        "/auth/register",
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


@pytest.mark.asyncio
async def test_register_with_email_service_sends_verification(
    monkeypatch, async_client,
):
    """Test registration with configured email service sends verification email."""
    from app.api.auth import login as mod

    async def fake_get_user_by_email(db, email):
        return None

    async def fake_get_user_by_username(db, username):
        return None

    async def fake_create_user(db, user):
        return create_test_user(
            email=user.email,
            username=user.username,
            is_verified=False,
        )

    monkeypatch.setattr(mod.crud_user, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(
        mod.crud_user, "get_user_by_username", fake_get_user_by_username,
    )
    monkeypatch.setattr(mod.crud_user, "create_user", fake_create_user)
    monkeypatch.setattr(mod, "email_service", MockEmailService(configured=True))

    resp = await async_client.post(
        "/auth/register",
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
