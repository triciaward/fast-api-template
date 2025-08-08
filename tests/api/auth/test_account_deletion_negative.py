import types
from uuid import UUID

import pytest


def _user_deleted():
    return types.SimpleNamespace(
        id=UUID("00000000-0000-0000-0000-0000000000ad"),
        email="user@example.com",
        username="user",
        is_deleted=True,
        deletion_requested_at=None,
        deletion_confirmed_at=None,
        deletion_scheduled_for=None,
    )


def _user_pending():
    return types.SimpleNamespace(
        id=UUID("00000000-0000-0000-0000-0000000000ad"),
        email="user@example.com",
        username="user",
        is_deleted=False,
        deletion_requested_at="2025-01-01T00:00:00Z",
        deletion_confirmed_at=None,
        deletion_scheduled_for=None,
    )


@pytest.mark.asyncio
async def test_confirm_deletion_already_deleted(monkeypatch, async_client):
    from app.api.auth import account_deletion as ad
    from app.crud.auth import user as crud_user

    async def fake_verify_deletion_token(db, token):
        return str(UUID("00000000-0000-0000-0000-0000000000ad"))

    async def fake_get_user_by_id(db, uid):
        return _user_deleted()

    esvc = types.SimpleNamespace(
        is_configured=lambda: True,
        verify_deletion_token=fake_verify_deletion_token,
    )

    monkeypatch.setattr(ad, "email_service", esvc)
    monkeypatch.setattr(crud_user, "get_user_by_id", fake_get_user_by_id)

    resp = await async_client.post(
        "/auth/confirm-deletion",
        json={"token": "tok"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["deletion_confirmed"] is False
    assert "already been deleted" in data["message"]


@pytest.mark.asyncio
async def test_confirm_deletion_db_failure(monkeypatch, async_client):
    from app.api.auth import account_deletion as ad
    from app.crud.auth import user as crud_user

    async def fake_verify_deletion_token(db, token):
        return str(UUID("00000000-0000-0000-0000-0000000000ad"))

    async def fake_get_user_by_id(db, uid):
        return _user_pending()

    async def fake_confirm_account_deletion(db, uid):
        return False

    esvc = types.SimpleNamespace(
        is_configured=lambda: True,
        verify_deletion_token=fake_verify_deletion_token,
    )

    monkeypatch.setattr(ad, "email_service", esvc)
    monkeypatch.setattr(crud_user, "get_user_by_id", fake_get_user_by_id)
    monkeypatch.setattr(
        crud_user, "confirm_account_deletion", fake_confirm_account_deletion,
    )

    resp = await async_client.post(
        "/auth/confirm-deletion",
        json={"token": "tok"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["deletion_confirmed"] is False
    assert data["message"].startswith("Failed to confirm account deletion")
