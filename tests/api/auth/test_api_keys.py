import types
from uuid import UUID

import pytest


def _user():
    return types.SimpleNamespace(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        email="user@example.com",
        username="user",
        is_superuser=False,
        oauth_provider=None,
    )


class FakeAPIKey:
    def __init__(self, idx: str | None = None, label: str = "my key") -> None:
        key_suffix = idx or "aa"
        self.id = UUID(f"00000000-0000-0000-0000-0000000000{key_suffix}")
        self.label = label
        self.scopes: list[str] = []
        self.user_id = UUID("00000000-0000-0000-0000-000000000001")
        self.is_active = True
        self.created_at = "2025-01-01T00:00:00Z"
        self.expires_at = None
        self.fingerprint = f"fp{key_suffix}"


@pytest.mark.asyncio
async def test_create_api_key_success(monkeypatch, async_client):
    from app.api.auth import api_keys as api_keys_mod
    from app.api.users import auth as users_auth
    from app.main import app

    app.dependency_overrides[users_auth.get_current_user] = lambda: _user()

    async def fake_create_api_key(db, api_key_data, user_id, raw_key):
        return FakeAPIKey("aa", label=api_key_data.label)

    monkeypatch.setattr(
        api_keys_mod.crud_api_key,
        "create_api_key",
        fake_create_api_key,
    )
    # generate_api_key is imported inside the function from app.core.security
    import app.core.security as core_security  # type: ignore

    monkeypatch.setattr(core_security, "generate_api_key", lambda: "RAWKEY")

    resp = await async_client.post(
        "/auth/api-keys",
        json={"label": "my key"},
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert resp.status_code == 201
    data = resp.json()
    assert data["raw_key"] == "RAWKEY"
    assert data["api_key"]["label"] == "my key"


@pytest.mark.asyncio
async def test_create_api_key_failure(monkeypatch, async_client):
    from app.api.auth import api_keys as api_keys_mod
    from app.api.users import auth as users_auth
    from app.main import app

    app.dependency_overrides[users_auth.get_current_user] = lambda: _user()
    import app.core.security as core_security  # type: ignore

    monkeypatch.setattr(core_security, "generate_api_key", lambda: "RAWKEY")

    async def fake_create(*args, **kwargs):
        raise RuntimeError("db down")

    monkeypatch.setattr(api_keys_mod.crud_api_key, "create_api_key", fake_create)

    resp = await async_client.post(
        "/auth/api-keys",
        json={"label": "err"},
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert resp.status_code == 500


@pytest.mark.asyncio
async def test_list_api_keys_pagination(monkeypatch, async_client):
    from app.api.auth import api_keys as api_keys_mod
    from app.api.users import auth as users_auth
    from app.main import app

    app.dependency_overrides[users_auth.get_current_user] = lambda: _user()

    async def fake_get_user_api_keys(db, user_id, skip, limit):
        return [FakeAPIKey("01", label="k1"), FakeAPIKey("02", label="k2")]

    async def fake_count_user_api_keys(db, user_id):
        return 10

    monkeypatch.setattr(
        api_keys_mod.crud_api_key,
        "get_user_api_keys",
        fake_get_user_api_keys,
    )
    monkeypatch.setattr(
        api_keys_mod.crud_api_key,
        "count_user_api_keys",
        fake_count_user_api_keys,
    )

    resp = await async_client.get(
        "/auth/api-keys?page=1&size=2",
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert resp.status_code == 200
    data = resp.json()
    assert data["metadata"]["page"] == 1
    assert len(data["items"]) == 2
    assert data["metadata"]["total"] == 10


@pytest.mark.asyncio
async def test_deactivate_api_key_not_found(monkeypatch, async_client):
    from app.api.auth import api_keys as api_keys_mod
    from app.api.users import auth as users_auth
    from app.main import app

    app.dependency_overrides[users_auth.get_current_user] = lambda: _user()

    async def fake_deactivate(db, key_id, user_id):
        return False

    monkeypatch.setattr(
        api_keys_mod.crud_api_key,
        "deactivate_api_key",
        fake_deactivate,
    )

    resp = await async_client.delete(
        "/auth/api-keys/key123",
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_deactivate_api_key_success(monkeypatch, async_client):
    from app.api.auth import api_keys as api_keys_mod
    from app.api.users import auth as users_auth
    from app.main import app

    app.dependency_overrides[users_auth.get_current_user] = lambda: _user()

    async def fake_deactivate(db, key_id, user_id):
        return True

    monkeypatch.setattr(
        api_keys_mod.crud_api_key,
        "deactivate_api_key",
        fake_deactivate,
    )

    resp = await async_client.delete(
        "/auth/api-keys/key123",
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_rotate_api_key_not_found(monkeypatch, async_client):
    from app.api.auth import api_keys as api_keys_mod
    from app.api.users import auth as users_auth
    from app.main import app

    app.dependency_overrides[users_auth.get_current_user] = lambda: _user()

    async def fake_rotate(db, key_id, user_id):
        return None, None

    monkeypatch.setattr(api_keys_mod.crud_api_key, "rotate_api_key", fake_rotate)

    resp = await async_client.post(
        "/auth/api-keys/key123/rotate",
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_rotate_api_key_success(monkeypatch, async_client):
    from app.api.auth import api_keys as api_keys_mod
    from app.api.users import auth as users_auth
    from app.main import app

    app.dependency_overrides[users_auth.get_current_user] = lambda: _user()

    async def fake_rotate(db, key_id, user_id):
        return FakeAPIKey("bb", label="rotated"), "NEWRAW"

    monkeypatch.setattr(api_keys_mod.crud_api_key, "rotate_api_key", fake_rotate)

    resp = await async_client.post(
        "/auth/api-keys/key123/rotate",
        headers={"authorization": "Bearer t", "user-agent": "pytest"},
    )
    app.dependency_overrides.clear()
    assert resp.status_code == 200
    data = resp.json()
    assert data["new_raw_key"] == "NEWRAW"
    assert data["api_key"]["label"] == "rotated"
