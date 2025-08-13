"""Password management tests (forgot, reset, change password)."""

import types

import pytest

from tests.utils.auth_helpers import (
    MockEmailService,
    create_test_user,
    override_dependency,
)

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_forgot_password_existing_user_success(monkeypatch, async_client):
    """Test forgot password for existing user with configured email service."""
    from app.api.auth import password_management as mod

    user = create_test_user(email="user@example.com")

    async def fake_get_user_by_email(db, email):
        return user

    async def fake_create_password_reset_token(db, user_id):
        return "reset_token_123"

    email_service = MockEmailService(configured=True)
    email_service.create_password_reset_token = fake_create_password_reset_token

    monkeypatch.setattr(mod.crud_user, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(mod, "email_service", email_service)

    resp = await async_client.post(
        "/api/auth/forgot-password",
        json={"email": "user@example.com"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["email_sent"] is True


@pytest.mark.asyncio
async def test_forgot_password_nonexistent_user_returns_generic(
    monkeypatch,
    async_client,
):
    """Test forgot password for nonexistent user returns generic success."""
    from app.api.auth import password_management as mod

    async def fake_get_user_by_email(db, email):
        return None

    monkeypatch.setattr(mod.crud_user, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(mod, "email_service", MockEmailService(configured=True))

    resp = await async_client.post(
        "/api/auth/forgot-password",
        json={"email": "nope@example.com"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["email_sent"] is True


@pytest.mark.asyncio
async def test_forgot_password_service_unavailable(monkeypatch, async_client):
    """Test forgot password when email service is not configured."""
    from app.api.auth import password_management as mod

    user = create_test_user(email="user@example.com")

    async def fake_get_user_by_email(db, email):
        return user

    monkeypatch.setattr(mod.crud_user, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(mod, "email_service", MockEmailService(configured=False))

    resp = await async_client.post(
        "/api/auth/forgot-password",
        json={"email": "user@example.com"},
    )
    assert resp.status_code == 200
    assert resp.json()["email_sent"] is False


@pytest.mark.asyncio
async def test_forgot_password_oauth_user_blocked(monkeypatch, async_client):
    """Test forgot password is blocked for OAuth users."""
    from app.api.auth import password_management as mod

    user = create_test_user(email="user@example.com", oauth_provider="google")

    async def fake_get_user_by_email(db, email):
        return user

    monkeypatch.setattr(mod.crud_user, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(mod, "email_service", MockEmailService(configured=True))

    resp = await async_client.post(
        "/api/auth/forgot-password",
        json={"email": "user@example.com"},
    )
    assert resp.status_code == 200
    # Should return generic success even for OAuth users for security
    assert resp.json()["email_sent"] is True


@pytest.mark.asyncio
async def test_reset_password_happy_path(monkeypatch, async_client):
    """Test successful password reset with valid token."""
    from app.api.auth import password_management as mod

    user = create_test_user()

    async def verify_password_reset_token(db, token):
        return user.id

    email_service = MockEmailService(configured=True)
    email_service.verify_password_reset_token = verify_password_reset_token

    async def fake_get_user_by_id(db, user_id):
        return user

    async def fake_reset_user_password(db, user_id, new_password):
        return True

    monkeypatch.setattr(mod, "email_service", email_service)
    monkeypatch.setattr(mod.crud_user, "get_user_by_id", fake_get_user_by_id)
    monkeypatch.setattr(mod.crud_user, "reset_user_password", fake_reset_user_password)

    resp = await async_client.post(
        "/api/auth/reset-password",
        json={"token": "valid_token", "new_password": "Password123!"},
    )
    assert resp.status_code == 200
    assert resp.json()["password_reset"] is True


@pytest.mark.asyncio
async def test_reset_password_invalid_token(monkeypatch, async_client):
    """Test password reset with invalid token."""
    from app.api.auth import password_management as mod

    async def verify_password_reset_token(db, token):
        return None

    email_service = MockEmailService(configured=True)
    email_service.verify_password_reset_token = verify_password_reset_token

    monkeypatch.setattr(mod, "email_service", email_service)

    resp = await async_client.post(
        "/api/auth/reset-password",
        json={"token": "invalid_token", "new_password": "Password123!"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["password_reset"] is False
    assert "invalid or expired" in body["message"].lower()


@pytest.mark.asyncio
async def test_reset_password_tampered_token(monkeypatch, async_client):
    """Test password reset with tampered token raises exception."""
    from app.api.auth import password_management as mod

    async def verify_password_reset_token(db, token):
        raise Exception("signature mismatch")

    email_service = MockEmailService(configured=True)
    email_service.verify_password_reset_token = verify_password_reset_token

    monkeypatch.setattr(mod, "email_service", email_service)

    resp = await async_client.post(
        "/api/auth/reset-password",
        json={"token": "tampered_token", "new_password": "Password123!"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["password_reset"] is False
    assert "invalid" in body["message"].lower()


@pytest.mark.asyncio
async def test_change_password_success(monkeypatch, async_client):
    """Test successful password change for authenticated user."""
    from app.api.auth import password_management as mod
    from app.main import app

    current_user = create_test_user()

    async def fake_get_current_user():
        return current_user

    async def fake_get_user_by_email(db, email):
        return types.SimpleNamespace(hashed_password="old_hash", id=current_user.id)

    async def fake_change_user_password(db, user_id, new_password):
        return True

    cleanup = override_dependency(app, mod.get_current_user, fake_get_current_user)
    monkeypatch.setattr(mod.crud_user, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(
        mod.crud_user,
        "update_user_password",
        fake_change_user_password,
    )
    monkeypatch.setattr(mod, "verify_password", lambda p, h: True)

    try:
        resp = await async_client.post(
            "/api/auth/change-password",
            json={"current_password": "old_password", "new_password": "Password123!"},
            headers={"authorization": "Bearer token", "user-agent": "pytest"},
        )
        assert resp.status_code == 200
        assert "successfully" in resp.json()["detail"].lower()
    finally:
        cleanup()


@pytest.mark.asyncio
async def test_change_password_incorrect_current(monkeypatch, async_client):
    """Test password change with incorrect current password."""
    from app.api.auth import password_management as mod
    from app.main import app

    current_user = create_test_user()

    async def fake_get_current_user():
        return current_user

    async def fake_get_user_by_email(db, email):
        return types.SimpleNamespace(hashed_password="hash", id=current_user.id)

    cleanup = override_dependency(app, mod.get_current_user, fake_get_current_user)
    monkeypatch.setattr(mod.crud_user, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(mod, "verify_password", lambda p, h: False)

    try:
        resp = await async_client.post(
            "/api/auth/change-password",
            json={"current_password": "wrong", "new_password": "Password123!"},
            headers={"authorization": "Bearer token", "user-agent": "pytest"},
        )
        assert resp.status_code == 400
        assert "incorrect current password" in resp.json()["error"]["message"].lower()
    finally:
        cleanup()


@pytest.mark.asyncio
async def test_change_password_oauth_user_denied(monkeypatch, async_client):
    """Test password change is denied for OAuth users."""
    from app.api.auth import password_management as mod
    from app.main import app

    current_user = create_test_user(oauth_provider="google")

    async def fake_get_current_user():
        return current_user

    cleanup = override_dependency(app, mod.get_current_user, fake_get_current_user)

    try:
        resp = await async_client.post(
            "/api/auth/change-password",
            json={"current_password": "old", "new_password": "Password123!"},
            headers={"authorization": "Bearer token", "user-agent": "pytest"},
        )
        assert resp.status_code == 400
        assert (
            "oauth users cannot change password"
            in resp.json()["error"]["message"].lower()
        )
    finally:
        cleanup()
