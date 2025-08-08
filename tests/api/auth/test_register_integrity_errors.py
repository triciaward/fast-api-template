import pytest
from sqlalchemy.exc import IntegrityError

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_register_integrity_email(monkeypatch, async_client):
    from app.api.auth import login as mod

    async def none(*a, **k):
        return None

    async def boom(*a, **k):
        raise IntegrityError("email", None, None)

    monkeypatch.setattr(mod.crud_user, "get_user_by_email", none)
    monkeypatch.setattr(mod.crud_user, "get_user_by_username", none)
    monkeypatch.setattr(mod.crud_user, "create_user", boom)

    r = await async_client.post(
        "/auth/register",
        json={
            "email": "e@example.com",
            "username": "zetauser",
            "password": "Passw0rd!",
        },
        headers={"user-agent": "pytest"},
    )
    assert r.status_code == 400
    assert "email already" in r.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_register_integrity_username(monkeypatch, async_client):
    from app.api.auth import login as mod

    async def none(*a, **k):
        return None

    async def boom(*a, **k):
        raise IntegrityError("username", None, None)

    monkeypatch.setattr(mod.crud_user, "get_user_by_email", none)
    monkeypatch.setattr(mod.crud_user, "get_user_by_username", none)
    monkeypatch.setattr(mod.crud_user, "create_user", boom)

    r = await async_client.post(
        "/auth/register",
        json={
            "email": "e2@example.com",
            "username": "zetaname",
            "password": "Passw0rd!",
        },
        headers={"user-agent": "pytest"},
    )
    assert r.status_code == 400
    assert "username" in r.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_register_integrity_general(monkeypatch, async_client):
    from app.api.auth import login as mod

    async def none(*a, **k):
        return None

    async def boom(*a, **k):
        raise IntegrityError("constraint", None, None)

    monkeypatch.setattr(mod.crud_user, "get_user_by_email", none)
    monkeypatch.setattr(mod.crud_user, "get_user_by_username", none)
    monkeypatch.setattr(mod.crud_user, "create_user", boom)

    r = await async_client.post(
        "/auth/register",
        json={"email": "e3@example.com", "username": "zetaok", "password": "Passw0rd!"},
        headers={"user-agent": "pytest"},
    )
    assert r.status_code == 400
    assert "constraint" in r.json()["error"]["message"].lower()
