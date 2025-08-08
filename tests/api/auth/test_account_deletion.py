import types

import pytest


def _user(email="user@example.com", pending=False, deleted=False):
    return types.SimpleNamespace(
        id="u1",
        email=email,
        username="user",
        is_deleted=deleted,
        deletion_requested_at=("2025-01-01T00:00:00Z" if pending else None),
        deletion_confirmed_at=None,
        deletion_scheduled_for=None,
        oauth_provider=None,
    )


@pytest.mark.asyncio
async def test_request_account_deletion_unconfigured_email(monkeypatch, async_client):
    from app.api.auth import account_deletion as ad
    from app.crud.auth import user as crud_user

    async def fake_get_user_by_email(db, email):
        return _user(email)

    monkeypatch.setattr(crud_user, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(
        ad,
        "email_service",
        types.SimpleNamespace(is_configured=lambda: False),
    )

    resp = await async_client.post(
        "/auth/request-deletion",
        json={"email": "user@example.com"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    assert resp.json()["email_sent"] is False


@pytest.mark.asyncio
async def test_confirm_account_deletion_invalid_token(monkeypatch, async_client):
    from app.api.auth import account_deletion as ad

    esvc = types.SimpleNamespace(
        is_configured=lambda: True,
        verify_deletion_token=lambda db, tok: None,
    )
    monkeypatch.setattr(ad, "email_service", esvc)

    resp = await async_client.post(
        "/auth/confirm-deletion",
        json={"token": "bad"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["deletion_confirmed"] is False


@pytest.mark.asyncio
async def test_cancel_account_deletion_no_pending(monkeypatch, async_client):
    from app.crud.auth import user as crud_user

    async def fake_get_user_by_email(db, email):
        return _user(email, pending=False)

    monkeypatch.setattr(crud_user, "get_user_by_email", fake_get_user_by_email)

    resp = await async_client.post(
        "/auth/cancel-deletion",
        json={"email": "user@example.com"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    assert resp.json()["deletion_cancelled"] is True
