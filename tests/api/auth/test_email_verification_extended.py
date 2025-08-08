import types
from uuid import UUID

import pytest

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_resend_verification_branches(monkeypatch, async_client):
    from app.api.auth import email_verification as ev
    from app.crud.auth import user as crud_user

    # User not found -> 404
    async def none_user(db, email):
        return None

    monkeypatch.setattr(crud_user, "get_user_by_email", none_user)
    r = await async_client.post(
        "/auth/resend-verification",
        json={"email": "nobody@example.com"},
        headers={"user-agent": "pytest"},
    )
    assert r.status_code == 404

    # Already verified -> email_sent False
    async def verified_user(db, email):
        return types.SimpleNamespace(id=UUID(int=1), email=email, username="u", is_verified=True)

    monkeypatch.setattr(crud_user, "get_user_by_email", verified_user)
    r2 = await async_client.post(
        "/auth/resend-verification",
        json={"email": "user@example.com"},
        headers={"user-agent": "pytest"},
    )
    assert r2.status_code == 200 and r2.json()["email_sent"] is False

    # Not configured -> email_sent False
    async def unverified_user(db, email):
        return types.SimpleNamespace(id=UUID(int=1), email=email, username="u", is_verified=False)

    monkeypatch.setattr(crud_user, "get_user_by_email", unverified_user)
    monkeypatch.setattr(ev, "email_service", None)
    r3 = await async_client.post(
        "/auth/resend-verification",
        json={"email": "user@example.com"},
        headers={"user-agent": "pytest"},
    )
    assert r3.status_code == 200 and r3.json()["email_sent"] is False

    # Token creation fails -> email_sent False
    async def create_verification_token_none(db, uid):
        return None

    esvc = types.SimpleNamespace(
        is_configured=lambda: True,
        create_verification_token=create_verification_token_none,
        send_verification_email=lambda e, u, t: False,
    )
    monkeypatch.setattr(ev, "email_service", esvc)
    r4 = await async_client.post(
        "/auth/resend-verification",
        json={"email": "user@example.com"},
        headers={"user-agent": "pytest"},
    )
    assert r4.status_code == 200 and r4.json()["email_sent"] is False

    # Email send succeeds -> email_sent True
    async def create_verification_token_ok(db, uid):
        return "tok"

    esvc_ok = types.SimpleNamespace(
        is_configured=lambda: True,
        create_verification_token=create_verification_token_ok,
        send_verification_email=lambda e, u, t: True,
    )
    monkeypatch.setattr(ev, "email_service", esvc_ok)
    r5 = await async_client.post(
        "/auth/resend-verification",
        json={"email": "user@example.com"},
        headers={"user-agent": "pytest"},
    )
    assert r5.status_code == 200 and r5.json()["email_sent"] is True


@pytest.mark.asyncio
async def test_verify_email_branches(monkeypatch, async_client):
    from app.api.auth import email_verification as ev
    from app.crud.auth import user as crud_user

    # Not configured -> verified False
    monkeypatch.setattr(ev, "email_service", None)
    r = await async_client.post(
        "/auth/verify-email",
        json={"token": "tok"},
        headers={"user-agent": "pytest"},
    )
    assert r.status_code == 200 and r.json()["verified"] is False

    # Invalid token -> verified False
    async def verify_token_bad(db, token):
        return None

    esvc = types.SimpleNamespace(is_configured=lambda: True, verify_token=verify_token_bad)
    monkeypatch.setattr(ev, "email_service", esvc)
    r2 = await async_client.post(
        "/auth/verify-email",
        json={"token": "tok"},
        headers={"user-agent": "pytest"},
    )
    assert r2.status_code == 200 and r2.json()["verified"] is False

    # User not found -> verified False
    async def verify_token_ok(db, token):
        return str(UUID(int=1))

    async def get_user_none(db, uid):
        return None

    esvc2 = types.SimpleNamespace(is_configured=lambda: True, verify_token=verify_token_ok)
    monkeypatch.setattr(ev, "email_service", esvc2)
    monkeypatch.setattr(crud_user, "get_user_by_id", get_user_none)
    r3 = await async_client.post(
        "/auth/verify-email",
        json={"token": "tok"},
        headers={"user-agent": "pytest"},
    )
    assert r3.status_code == 200 and r3.json()["verified"] is False

    # Already verified -> verified True
    async def get_user_verified(db, uid):
        return types.SimpleNamespace(id=UUID(int=1), is_verified=True)

    monkeypatch.setattr(crud_user, "get_user_by_id", get_user_verified)
    r4 = await async_client.post(
        "/auth/verify-email",
        json={"token": "tok"},
        headers={"user-agent": "pytest"},
    )
    assert r4.status_code == 200 and r4.json()["verified"] is True

    # Verify user fails -> verified False
    async def get_user_unverified(db, uid):
        return types.SimpleNamespace(id=UUID(int=1), is_verified=False)

    async def verify_user_fail(db, uid):
        return False

    monkeypatch.setattr(crud_user, "get_user_by_id", get_user_unverified)
    monkeypatch.setattr(crud_user, "verify_user", verify_user_fail)
    r5 = await async_client.post(
        "/auth/verify-email",
        json={"token": "tok"},
        headers={"user-agent": "pytest"},
    )
    assert r5.status_code == 200 and r5.json()["verified"] is False


