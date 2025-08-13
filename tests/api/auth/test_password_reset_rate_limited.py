import types

import pytest


def _user():
    return types.SimpleNamespace(
        id="u1",
        email="user@example.com",
        username="user",
        oauth_provider=None,
    )


@pytest.mark.asyncio
async def test_forgot_password_success_with_rate_limit_enabled(
    monkeypatch,
    async_client,
):
    from app.api.auth import password_management as pm
    from app.core.config import settings
    from app.crud.auth import user as crud_user

    monkeypatch.setattr(settings, "ENABLE_RATE_LIMITING", True)

    async def fake_get_user_by_email(db, email):
        return _user()

    async def fake_create_password_reset_token(db, uid):
        return "rtok"

    esvc = types.SimpleNamespace(
        is_configured=lambda: True,
        create_password_reset_token=fake_create_password_reset_token,
        send_password_reset_email=lambda email, username, tok: True,
    )

    monkeypatch.setattr(crud_user, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(pm, "email_service", esvc)

    resp = await async_client.post(
        "/api/auth/forgot-password",
        json={"email": "user@example.com"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    assert resp.json()["email_sent"] is True


@pytest.mark.asyncio
async def test_reset_password_success_with_rate_limit_enabled(
    monkeypatch,
    async_client,
):
    from app.api.auth import password_management as pm
    from app.core.config import settings
    from app.crud.auth import user as crud_user

    monkeypatch.setattr(settings, "ENABLE_RATE_LIMITING", True)

    async def fake_verify_password_reset_token(db, tok):
        return "u1"

    async def fake_get_user_by_id(db, uid):
        return _user()

    async def fake_reset_user_password(db, uid, new_pw):
        return True

    esvc = types.SimpleNamespace(
        is_configured=lambda: True,
        verify_password_reset_token=fake_verify_password_reset_token,
    )

    monkeypatch.setattr(pm, "email_service", esvc)
    monkeypatch.setattr(crud_user, "get_user_by_id", fake_get_user_by_id)
    monkeypatch.setattr(crud_user, "reset_user_password", fake_reset_user_password)

    resp = await async_client.post(
        "/api/auth/reset-password",
        json={"token": "rtok", "new_password": "StrongPass123!"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    assert resp.json()["password_reset"] is True
