import types
from datetime import datetime, timezone
from uuid import UUID

import pytest


def _now_iso():
    return datetime.now(timezone.utc)


def _user_obj():
    return types.SimpleNamespace(
        id=UUID("00000000-0000-0000-0000-0000000000aa"),
        email="new@example.com",
        username="newuser",
        is_superuser=False,
        is_verified=False,
        is_deleted=False,
        created_at=_now_iso(),
        oauth_provider=None,
        hashed_password="hash",
    )


@pytest.mark.asyncio
async def test_register_email_exists(monkeypatch, async_client):
    from app.api.auth import login as login_module

    async def fake_get_user_by_email(db, email):
        return _user_obj()

    monkeypatch.setattr(
        login_module.crud_user,
        "get_user_by_email",
        fake_get_user_by_email,
    )

    resp = await async_client.post(
        "/auth/register",
        json={
            "email": "new@example.com",
            "username": "newuser",
            "password": "Password123!",
            "is_superuser": False,
        },
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert (
        body.get("error", {}).get("message", "").startswith("Email already registered")
    )


@pytest.mark.asyncio
async def test_register_username_taken(monkeypatch, async_client):
    from app.api.auth import login as login_module

    async def fake_get_user_by_email(db, email):
        return None

    async def fake_get_user_by_username(db, username):
        return _user_obj()

    monkeypatch.setattr(
        login_module.crud_user,
        "get_user_by_email",
        fake_get_user_by_email,
    )
    monkeypatch.setattr(
        login_module.crud_user,
        "get_user_by_username",
        fake_get_user_by_username,
    )

    resp = await async_client.post(
        "/auth/register",
        json={
            "email": "new@example.com",
            "username": "newuser",
            "password": "Password123!",
            "is_superuser": False,
        },
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body.get("error", {}).get("message", "").startswith("Username already taken")


@pytest.mark.asyncio
async def test_register_success_without_email_service(monkeypatch, async_client):
    from app.api.auth import login as login_module

    async def fake_get_user_by_email(db, email):
        return None

    async def fake_get_user_by_username(db, username):
        return None

    async def fake_create_user(db, user):
        return _user_obj()

    # email service not configured
    monkeypatch.setattr(
        login_module,
        "email_service",
        types.SimpleNamespace(is_configured=lambda: False),
    )
    monkeypatch.setattr(
        login_module.crud_user,
        "get_user_by_email",
        fake_get_user_by_email,
    )
    monkeypatch.setattr(
        login_module.crud_user,
        "get_user_by_username",
        fake_get_user_by_username,
    )
    monkeypatch.setattr(login_module.crud_user, "create_user", fake_create_user)

    resp = await async_client.post(
        "/auth/register",
        json={
            "email": "new@example.com",
            "username": "newuser",
            "password": "Password123!",
            "is_superuser": False,
        },
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@example.com"
    assert data["username"] == "newuser"


@pytest.mark.asyncio
async def test_register_success_with_email_service(monkeypatch, async_client):
    from app.api.auth import login as login_module

    async def fake_get_user_by_email(db, email):
        return None

    async def fake_get_user_by_username(db, username):
        return None

    async def fake_create_user(db, user):
        return _user_obj()

    async def fake_create_verification_token(db, user_id):
        return "tok"

    esvc = types.SimpleNamespace(
        is_configured=lambda: True,
        create_verification_token=fake_create_verification_token,
        send_verification_email=lambda *a, **k: True,
    )

    monkeypatch.setattr(login_module, "email_service", esvc)
    monkeypatch.setattr(
        login_module.crud_user,
        "get_user_by_email",
        fake_get_user_by_email,
    )
    monkeypatch.setattr(
        login_module.crud_user,
        "get_user_by_username",
        fake_get_user_by_username,
    )
    monkeypatch.setattr(login_module.crud_user, "create_user", fake_create_user)

    resp = await async_client.post(
        "/auth/register",
        json={
            "email": "new@example.com",
            "username": "newuser",
            "password": "Password123!",
            "is_superuser": False,
        },
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code == 201
