import types

import pytest


@pytest.mark.asyncio
async def test_forgot_password_email_service_unconfigured(monkeypatch, async_client):
    from app.api.auth import password_management as pm

    # Non-existent user path returns email_sent=True regardless of email service
    # So ensure a user exists to hit the is_configured branch
    from app.crud.auth import user as crud_user

    async def fake_get_user_by_email(db, email):
        return types.SimpleNamespace(
            id="u1",
            email=email,
            username="user",
            oauth_provider=None,
        )

    monkeypatch.setattr(crud_user, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(pm.email_service, "is_configured", lambda: False)

    resp = await async_client.post(
        "/api/auth/forgot-password",
        json={"email": "nobody@example.com"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["email_sent"] is False


@pytest.mark.asyncio
async def test_forgot_password_token_creation_failure(monkeypatch, async_client):
    from app.api.auth import password_management as pm
    from app.crud.auth import user as crud_user

    # Mock user exists and is non-OAuth
    user = types.SimpleNamespace(
        id="u1",
        email="u@example.com",
        username="u",
        oauth_provider=None,
    )

    async def fake_get_user_by_email(db, email):
        return user

    monkeypatch.setattr(crud_user, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(pm.email_service, "is_configured", lambda: True)

    async def fake_create_token(db, user_id):
        return None

    monkeypatch.setattr(
        pm.email_service,
        "create_password_reset_token",
        fake_create_token,
    )

    resp = await async_client.post(
        "/api/auth/forgot-password",
        json={"email": "u@example.com"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["email_sent"] is False


@pytest.mark.asyncio
async def test_forgot_password_send_failure(monkeypatch, async_client):
    from app.api.auth import password_management as pm
    from app.crud.auth import user as crud_user

    # Mock user exists and is non-OAuth
    user = types.SimpleNamespace(
        id="u1",
        email="u@example.com",
        username="u",
        oauth_provider=None,
    )

    async def fake_get_user_by_email(db, email):
        return user

    monkeypatch.setattr(crud_user, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(pm.email_service, "is_configured", lambda: True)

    async def fake_create_token(db, user_id):
        return "tok"

    monkeypatch.setattr(
        pm.email_service,
        "create_password_reset_token",
        fake_create_token,
    )
    monkeypatch.setattr(
        pm.email_service,
        "send_password_reset_email",
        lambda *a, **k: False,
    )

    resp = await async_client.post(
        "/api/auth/forgot-password",
        json={"email": "u@example.com"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["email_sent"] is False
