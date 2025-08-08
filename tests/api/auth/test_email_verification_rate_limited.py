import types

import pytest


def _user(verified=False):
    return types.SimpleNamespace(
        id="u1",
        email="user@example.com",
        username="user",
        is_verified=verified,
    )


@pytest.mark.asyncio
async def test_resend_verification_success_with_rate_limit_enabled(
    monkeypatch, async_client,
):
    from app.api.auth import email_verification as ev
    from app.core.config import settings
    from app.crud.auth import user as crud_user

    # Enable rate limiting
    monkeypatch.setattr(settings, "ENABLE_RATE_LIMITING", True)

    async def fake_get_user_by_email(db, email):
        return _user(verified=False)

    async def fake_create_verification_token(db, uid):
        return "tok"

    esvc = types.SimpleNamespace(
        is_configured=lambda: True,
        create_verification_token=fake_create_verification_token,
        send_verification_email=lambda email, username, tok: True,
    )

    monkeypatch.setattr(crud_user, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(ev, "email_service", esvc)

    resp = await async_client.post(
        "/auth/resend-verification",
        json={"email": "user@example.com"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    assert resp.json()["email_sent"] is True


@pytest.mark.asyncio
async def test_verify_email_success_with_rate_limit_enabled(monkeypatch, async_client):
    from app.api.auth import email_verification as ev
    from app.core.config import settings
    from app.crud.auth import user as crud_user

    # Enable rate limiting
    monkeypatch.setattr(settings, "ENABLE_RATE_LIMITING", True)

    async def fake_verify_token(db, tok):
        return "u1"

    esvc = types.SimpleNamespace(
        is_configured=lambda: True,
        verify_token=fake_verify_token,
    )

    async def fake_get_user_by_id(db, uid):
        return _user(verified=False)

    async def fake_verify_user(db, uid):
        return True

    monkeypatch.setattr(ev, "email_service", esvc)
    monkeypatch.setattr(crud_user, "get_user_by_id", fake_get_user_by_id)
    monkeypatch.setattr(crud_user, "verify_user", fake_verify_user)

    resp = await async_client.post(
        "/auth/verify-email",
        json={"token": "tok"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    assert resp.json()["verified"] is True


@pytest.mark.asyncio
async def test_resend_verification_already_verified_with_rate_limit_enabled(
    monkeypatch, async_client,
):
    from app.api.auth import email_verification as ev
    from app.core.config import settings
    from app.crud.auth import user as crud_user

    monkeypatch.setattr(settings, "ENABLE_RATE_LIMITING", True)

    async def fake_get_user_by_email(db, email):
        return _user(verified=True)

    # email service should not be called, but keep configured
    esvc = types.SimpleNamespace(is_configured=lambda: True)

    monkeypatch.setattr(crud_user, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(ev, "email_service", esvc)

    resp = await async_client.post(
        "/auth/resend-verification",
        json={"email": "user@example.com"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["email_sent"] is False
    assert data["message"] == "User is already verified"


@pytest.mark.asyncio
async def test_verify_email_already_verified_with_rate_limit_enabled(
    monkeypatch, async_client,
):
    from app.api.auth import email_verification as ev
    from app.core.config import settings
    from app.crud.auth import user as crud_user

    monkeypatch.setattr(settings, "ENABLE_RATE_LIMITING", True)

    async def fake_verify_token(db, tok):
        return "u1"

    async def fake_get_user_by_id(db, uid):
        return _user(verified=True)

    esvc = types.SimpleNamespace(
        is_configured=lambda: True, verify_token=fake_verify_token,
    )
    monkeypatch.setattr(ev, "email_service", esvc)
    monkeypatch.setattr(crud_user, "get_user_by_id", fake_get_user_by_id)

    resp = await async_client.post(
        "/auth/verify-email",
        json={"token": "tok"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["verified"] is True
    assert data["message"] == "User is already verified"
