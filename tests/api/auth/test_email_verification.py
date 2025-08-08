import types

import pytest

pytestmark = pytest.mark.unit


def _user(verified: bool = False):
    return types.SimpleNamespace(
        id="11111111-1111-1111-1111-111111111111",
        email="u@example.com",
        username="user1",
        is_verified=verified,
    )


@pytest.mark.asyncio
async def test_resend_verification_user_not_found(monkeypatch, async_client):
    from app.api.auth import email_verification as mod

    async def fake_get_user_by_email(db, email):
        return None

    monkeypatch.setattr(mod.crud_user, "get_user_by_email", fake_get_user_by_email)
    resp = await async_client.post(
        "/auth/resend-verification", json={"email": "u@example.com"},
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] in {"user_not_found", "resource_not_found"}


@pytest.mark.asyncio
async def test_resend_verification_already_verified(monkeypatch, async_client):
    from app.api.auth import email_verification as mod

    async def fake_get_user_by_email(db, email):
        return _user(verified=True)

    monkeypatch.setattr(mod.crud_user, "get_user_by_email", fake_get_user_by_email)
    # Simulate email service configured; it won't be used
    monkeypatch.setattr(
        mod, "email_service", types.SimpleNamespace(is_configured=lambda: True),
    )
    resp = await async_client.post(
        "/auth/resend-verification", json={"email": "u@example.com"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["email_sent"] is False and "already verified" in body["message"].lower()


@pytest.mark.asyncio
async def test_resend_verification_sends_email(monkeypatch, async_client):
    from app.api.auth import email_verification as mod

    async def fake_get_user_by_email(db, email):
        return _user(verified=False)

    async def create_verification_token(db, uid):
        return "token123"

    email_service = types.SimpleNamespace(
        is_configured=lambda: True,
        create_verification_token=create_verification_token,
        send_verification_email=lambda email, username, token: True,
    )

    monkeypatch.setattr(mod.crud_user, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(mod, "email_service", email_service)

    resp = await async_client.post(
        "/auth/resend-verification", json={"email": "u@example.com"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["email_sent"] is True


@pytest.mark.asyncio
async def test_verify_email_happy_path(monkeypatch, async_client):
    from app.api.auth import email_verification as mod

    async def verify_token(db, token):
        return "11111111-1111-1111-1111-111111111111"

    email_service = types.SimpleNamespace(
        is_configured=lambda: True,
        verify_token=verify_token,
    )

    async def fake_get_user_by_id(db, user_id):
        return _user(verified=False)

    async def fake_verify_user(db, user_id):
        return True

    monkeypatch.setattr(mod, "email_service", email_service)
    monkeypatch.setattr(mod.crud_user, "get_user_by_id", fake_get_user_by_id)
    monkeypatch.setattr(mod.crud_user, "verify_user", fake_verify_user)

    resp = await async_client.post("/auth/verify-email", json={"token": "tok"})
    assert resp.status_code == 200
    assert resp.json()["verified"] is True


@pytest.mark.asyncio
async def test_verify_email_invalid_token(monkeypatch, async_client):
    from app.api.auth import email_verification as mod

    async def verify_token(db, token):
        return None

    email_service = types.SimpleNamespace(
        is_configured=lambda: True,
        verify_token=verify_token,
    )

    monkeypatch.setattr(mod, "email_service", email_service)
    resp = await async_client.post("/auth/verify-email", json={"token": "invalid"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["verified"] is False
    assert "invalid or expired" in body["message"].lower()


@pytest.mark.asyncio
async def test_verify_email_tampered_token(monkeypatch, async_client):
    from app.api.auth import email_verification as mod

    async def verify_token(db, token):
        raise Exception("token signature mismatch")

    email_service = types.SimpleNamespace(
        is_configured=lambda: True,
        verify_token=verify_token,
    )

    monkeypatch.setattr(mod, "email_service", email_service)
    resp = await async_client.post("/auth/verify-email", json={"token": "tampered"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["verified"] is False
    assert "invalid" in body["message"].lower()


@pytest.mark.asyncio
async def test_verify_email_user_not_found(monkeypatch, async_client):
    from app.api.auth import email_verification as mod

    async def verify_token(db, token):
        return "11111111-1111-1111-1111-111111111111"

    async def fake_get_user_by_id(db, user_id):
        return None

    email_service = types.SimpleNamespace(
        is_configured=lambda: True,
        verify_token=verify_token,
    )

    monkeypatch.setattr(mod, "email_service", email_service)
    monkeypatch.setattr(mod.crud_user, "get_user_by_id", fake_get_user_by_id)

    resp = await async_client.post("/auth/verify-email", json={"token": "tok"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["verified"] is False
    assert "user not found" in body["message"].lower()


@pytest.mark.asyncio
async def test_verify_email_already_verified(monkeypatch, async_client):
    from app.api.auth import email_verification as mod

    async def verify_token(db, token):
        return "11111111-1111-1111-1111-111111111111"

    async def fake_get_user_by_id(db, user_id):
        return _user(verified=True)

    email_service = types.SimpleNamespace(
        is_configured=lambda: True,
        verify_token=verify_token,
    )

    monkeypatch.setattr(mod, "email_service", email_service)
    monkeypatch.setattr(mod.crud_user, "get_user_by_id", fake_get_user_by_id)

    resp = await async_client.post("/auth/verify-email", json={"token": "tok"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["verified"] is True
    assert "already verified" in body["message"].lower()
