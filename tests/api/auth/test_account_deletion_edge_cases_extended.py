import types
from uuid import UUID

import pytest

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_request_deletion_email_service_unconfigured(monkeypatch, async_client):
    from app.api.auth import account_deletion as ad
    from app.crud.auth import user as crud_user

    async def fake_get_user_by_email(db, email):
        return types.SimpleNamespace(id=UUID(int=1), email=email, username="u", is_deleted=False, deletion_requested_at=None)

    monkeypatch.setattr(crud_user, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(ad, "email_service", None)

    resp = await async_client.post(
        "/auth/request-deletion",
        json={"email": "user@example.com"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    assert resp.json()["email_sent"] is False


@pytest.mark.asyncio
async def test_request_deletion_token_creation_failure(monkeypatch, async_client):
    from app.api.auth import account_deletion as ad
    from app.crud.auth import user as crud_user

    async def fake_get_user_by_email(db, email):
        return types.SimpleNamespace(id=UUID(int=1), email=email, username="u", is_deleted=False, deletion_requested_at=None)

    async def fake_create_deletion_token(db, uid):
        return None

    esvc = types.SimpleNamespace(is_configured=lambda: True, create_deletion_token=fake_create_deletion_token)

    monkeypatch.setattr(crud_user, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(ad, "email_service", esvc)

    resp = await async_client.post(
        "/auth/request-deletion",
        json={"email": "user@example.com"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    assert resp.json()["email_sent"] is False


@pytest.mark.asyncio
async def test_request_deletion_mark_failure(monkeypatch, async_client):
    from app.api.auth import account_deletion as ad
    from app.crud.auth import user as crud_user

    async def fake_get_user_by_email(db, email):
        return types.SimpleNamespace(id=UUID(int=1), email=email, username="u", is_deleted=False, deletion_requested_at=None)

    async def fake_create_deletion_token(db, uid):
        return "tok"

    async def fake_request_account_deletion(db, uid):
        return False

    esvc = types.SimpleNamespace(is_configured=lambda: True, create_deletion_token=fake_create_deletion_token)

    monkeypatch.setattr(crud_user, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(crud_user, "request_account_deletion", fake_request_account_deletion)
    monkeypatch.setattr(ad, "email_service", esvc)

    resp = await async_client.post(
        "/auth/request-deletion",
        json={"email": "user@example.com"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    assert resp.json()["email_sent"] is False


@pytest.mark.asyncio
async def test_request_deletion_email_send_failure(monkeypatch, async_client):
    from app.api.auth import account_deletion as ad
    from app.crud.auth import user as crud_user

    async def fake_get_user_by_email(db, email):
        return types.SimpleNamespace(id=UUID(int=1), email=email, username="u", is_deleted=False, deletion_requested_at=None)

    async def fake_create_deletion_token(db, uid):
        return "tok"

    async def fake_request_account_deletion(db, uid):
        return True

    esvc = types.SimpleNamespace(
        is_configured=lambda: True,
        create_deletion_token=fake_create_deletion_token,
        send_account_deletion_email=lambda email, username, token: False,
    )

    monkeypatch.setattr(crud_user, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(crud_user, "request_account_deletion", fake_request_account_deletion)
    monkeypatch.setattr(ad, "email_service", esvc)

    resp = await async_client.post(
        "/auth/request-deletion",
        json={"email": "user@example.com"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    assert resp.json()["email_sent"] is False


@pytest.mark.asyncio
async def test_confirm_deletion_unconfigured_service(monkeypatch, async_client):
    from app.api.auth import account_deletion as ad

    monkeypatch.setattr(ad, "email_service", None)
    resp = await async_client.post(
        "/auth/confirm-deletion",
        json={"token": "x"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    assert resp.json()["deletion_confirmed"] is False


@pytest.mark.asyncio
async def test_confirm_deletion_invalid_token(monkeypatch, async_client):
    from app.api.auth import account_deletion as ad

    async def fake_verify_deletion_token(db, token):
        return None

    esvc = types.SimpleNamespace(is_configured=lambda: True, verify_deletion_token=fake_verify_deletion_token)
    monkeypatch.setattr(ad, "email_service", esvc)

    resp = await async_client.post(
        "/auth/confirm-deletion",
        json={"token": "bad"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    assert resp.json()["deletion_confirmed"] is False


@pytest.mark.asyncio
async def test_cancel_deletion_fail_cancel(monkeypatch, async_client):
    from app.crud.auth import user as crud_user

    async def fake_get_user_by_email(db, email):
        return types.SimpleNamespace(
            id=UUID(int=1),
            email=email,
            username="u",
            is_deleted=False,
            deletion_requested_at="2025-01-01T00:00:00Z",
        )

    async def fake_cancel_account_deletion(db, uid):
        return False

    monkeypatch.setattr(crud_user, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(crud_user, "cancel_account_deletion", fake_cancel_account_deletion)

    resp = await async_client.post(
        "/auth/cancel-deletion",
        json={"email": "user@example.com"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 200
    assert resp.json()["deletion_cancelled"] is False


