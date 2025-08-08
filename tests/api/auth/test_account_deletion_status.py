import types

import pytest


def _user_state(pending=False, confirmed=False, deleted=False):
    return types.SimpleNamespace(
        is_deleted=deleted,
        deletion_requested_at=("2025-01-01T00:00:00Z" if pending else None),
        deletion_confirmed_at=("2025-01-02T00:00:00Z" if confirmed else None),
        deletion_scheduled_for=("2025-01-08T00:00:00Z" if confirmed else None),
    )


@pytest.mark.asyncio
async def test_deletion_status_user_not_found(monkeypatch, async_client):
    from app.crud.auth import user as crud_user

    async def fake_get_user_by_email(db, email):
        return None

    monkeypatch.setattr(crud_user, "get_user_by_email", fake_get_user_by_email)

    resp = await async_client.get(
        "/auth/deletion-status",
        params={"email": "nobody@example.com"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["deletion_requested"] is False
    assert data["deletion_confirmed"] is False
    assert data["can_cancel"] is False


@pytest.mark.asyncio
async def test_deletion_status_pending(monkeypatch, async_client):
    from app.crud.auth import user as crud_user

    async def fake_get_user_by_email(db, email):
        return _user_state(pending=True, confirmed=False, deleted=False)

    monkeypatch.setattr(crud_user, "get_user_by_email", fake_get_user_by_email)

    resp = await async_client.get(
        "/auth/deletion-status",
        params={"email": "user@example.com"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["deletion_requested"] is True
    assert data["can_cancel"] is True


@pytest.mark.asyncio
async def test_deletion_status_confirmed(monkeypatch, async_client):
    from app.crud.auth import user as crud_user

    async def fake_get_user_by_email(db, email):
        return _user_state(pending=True, confirmed=True, deleted=False)

    monkeypatch.setattr(crud_user, "get_user_by_email", fake_get_user_by_email)

    resp = await async_client.get(
        "/auth/deletion-status",
        params={"email": "user@example.com"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["deletion_requested"] is True
    assert data["deletion_confirmed"] is True
