import types

import pytest

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_read_current_user_with_valid_token(monkeypatch, async_client):
    # Build a minimal JWT for dependency to accept
    from app.api.users import auth as user_auth

    def fake_decode(token, key, algorithms):
        return {"sub": "user-123"}

    async def fake_get_user_by_id(db, user_id):
        # Provide fields compatible with UserResponse schema
        return types.SimpleNamespace(
            id="11111111-1111-1111-1111-111111111111",
            email="u@example.com",
            username="user123",
            is_verified=True,
            is_superuser=False,
            created_at="2025-01-01T00:00:00Z",
            is_deleted=False,
        )

    monkeypatch.setattr(user_auth.jwt, "decode", fake_decode)
    from app.crud.auth import user as crud_user

    monkeypatch.setattr(crud_user, "get_user_by_id", fake_get_user_by_id)

    # Inject Authorization header for OAuth2PasswordBearer
    resp = await async_client.get(
        "/api/users/me",
        headers={"authorization": "Bearer dummy", "user-agent": "pytest"},
    )
    assert resp.status_code == 200
    body = resp.json()
    # Accept any UUID since app may coerce types; ensure fields are present
    assert body["email"] == "u@example.com"
    assert body["username"] == "user123"


@pytest.mark.asyncio
async def test_read_current_user_api_key_success(monkeypatch, async_client):

    # Fake API key verification returning an object with required fields
    fake_db_api_key = types.SimpleNamespace(
        id="22222222-2222-2222-2222-222222222222",
        scopes=["read"],
        user_id="33333333-3333-3333-3333-333333333333",
        is_active=True,
        expires_at=None,
    )

    async def fake_verify_api_key_in_db(db, api_key):
        return fake_db_api_key

    async def fake_log_api_key_usage(**kwargs):
        return None

    from app.crud.auth import api_key as crud_api_key

    monkeypatch.setattr(crud_api_key, "verify_api_key_in_db", fake_verify_api_key_in_db)
    from app.services.monitoring import audit

    monkeypatch.setattr(audit, "log_api_key_usage", fake_log_api_key_usage)

    resp = await async_client.get(
        "/api/users/me/api-key",
        headers={"authorization": "Bearer TESTKEY", "user-agent": "pytest"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["key_id"] == "22222222-2222-2222-2222-222222222222"
