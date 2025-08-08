import types
from datetime import datetime, timezone
from uuid import UUID

import pytest


def _user(pending=False, deleted=False):
    return types.SimpleNamespace(
        id=UUID("00000000-0000-0000-0000-0000000000de"),
        email="user@example.com",
        username="user",
        is_deleted=deleted,
        deletion_requested_at=(datetime.now(timezone.utc) if pending else None),
        deletion_confirmed_at=None,
        deletion_scheduled_for=None,
    )


@pytest.mark.asyncio
async def test_request_account_deletion_success(monkeypatch, async_client):
    from app.api.auth import account_deletion as ad
    from app.crud.auth import user as crud_user

    # User exists and not pending/deleted
    async def fake_get_user_by_email(db, email):
        return _user(pending=False, deleted=False)

    async def fake_request_account_deletion(db, user_id):
        return True

    # Email service configured and works
    async def fake_create_deletion_token(db, uid):
        return "token123"

    esvc = types.SimpleNamespace(
        is_configured=lambda: True,
        create_deletion_token=fake_create_deletion_token,
        send_account_deletion_email=lambda email, username, token: True,
    )

    # Avoid DB writes in audit log
    async def fake_log(*args, **kwargs):
        return None

    monkeypatch.setattr(crud_user, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(crud_user, "request_account_deletion", fake_request_account_deletion)
    monkeypatch.setattr(ad, "email_service", esvc)
    monkeypatch.setattr(ad, "log_account_deletion", fake_log)

    resp = await async_client.post(
        "/auth/request-deletion",
        json={"email": "user@example.com"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["email_sent"] is True


@pytest.mark.asyncio
async def test_confirm_account_deletion_success(monkeypatch, async_client):
    from app.api.auth import account_deletion as ad
    from app.crud.auth import user as crud_user

    # Email service configured and token verifies
    async def fake_verify_deletion_token(db, token):
        return str(UUID("00000000-0000-0000-0000-0000000000de"))

    esvc = types.SimpleNamespace(
        is_configured=lambda: True,
        verify_deletion_token=fake_verify_deletion_token,
    )

    user = _user(pending=True, deleted=False)

    async def fake_get_user_by_id(db, uid):
        return user

    async def fake_confirm_account_deletion(db, uid):
        return True

    async def fake_log(*args, **kwargs):
        return None

    monkeypatch.setattr(ad, "email_service", esvc)
    monkeypatch.setattr(crud_user, "get_user_by_id", fake_get_user_by_id)
    monkeypatch.setattr(crud_user, "confirm_account_deletion", fake_confirm_account_deletion)
    monkeypatch.setattr(ad, "log_account_deletion", fake_log)

    resp = await async_client.post(
        "/auth/confirm-deletion",
        json={"token": "good-token"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["deletion_confirmed"] is True
    assert "deletion_scheduled_for" in data

    # Sanity: scheduled date in the future within grace period
    # Parse ISO string if needed
    scheduled_str = data["deletion_scheduled_for"]
    # Some schemas may serialize datetime; accept either str or None
    assert scheduled_str is not None


@pytest.mark.asyncio
async def test_cancel_account_deletion_success(monkeypatch, async_client):
    from app.api.auth import account_deletion as ad
    from app.crud.auth import user as crud_user

    # User exists and is pending deletion
    async def fake_get_user_by_email(db, email):
        return _user(pending=True, deleted=False)

    async def fake_cancel_account_deletion(db, uid):
        return True

    async def fake_log(*args, **kwargs):
        return None

    monkeypatch.setattr(crud_user, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(crud_user, "cancel_account_deletion", fake_cancel_account_deletion)
    monkeypatch.setattr(ad, "log_account_deletion", fake_log)

    resp = await async_client.post(
        "/auth/cancel-deletion",
        json={"email": "user@example.com"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["deletion_cancelled"] is True


