import types

import pytest

pytestmark = pytest.mark.unit


def _auth_ok(monkeypatch):
    from app.api.users import auth as user_auth

    def fake_decode(token, key, algorithms):
        return {"sub": "11111111-1111-1111-1111-111111111111"}

    async def fake_get_user_by_id(db, user_id):
        return types.SimpleNamespace(
            id="11111111-1111-1111-1111-111111111111",
            email="u@e.com",
        )

    monkeypatch.setattr(user_auth.jwt, "decode", fake_decode)
    from app.crud.auth import user as crud_user

    monkeypatch.setattr(crud_user, "get_user_by_id", fake_get_user_by_id)


@pytest.mark.asyncio
async def test_refresh_token_no_cookie(monkeypatch, async_client):

    _auth_ok(monkeypatch)

    # Force get_refresh_token_from_cookie to return None
    import app.services.auth.refresh_token as rt

    monkeypatch.setattr(rt, "get_refresh_token_from_cookie", lambda req: None)

    resp = await async_client.post(
        "/auth/refresh",
        headers={"authorization": "Bearer dummy", "user-agent": "pytest"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_user_sessions_happy(monkeypatch, async_client):

    _auth_ok(monkeypatch)

    # Return no current cookie and 2 sessions
    import app.services.auth.refresh_token as rt

    monkeypatch.setattr(rt, "get_refresh_token_from_cookie", lambda req: None)

    async def fake_get_user_sessions(db, user_id):
        return [
            types.SimpleNamespace(
                id="00000000-0000-0000-0000-000000000001",
                created_at="2025-01-01T00:00:00Z",
                device_info="Browser",
                ip_address="1.2.3.4",
                is_current=False,
            ),
            types.SimpleNamespace(
                id="00000000-0000-0000-0000-000000000002",
                created_at="2025-01-02T00:00:00Z",
                device_info="Browser",
                ip_address="1.2.3.5",
                is_current=True,
            ),
        ]

    from app.crud.auth import refresh_token as crud_rt

    monkeypatch.setattr(crud_rt, "get_user_sessions", fake_get_user_sessions)

    resp = await async_client.get(
        "/auth/sessions",
        headers={"authorization": "Bearer dummy", "user-agent": "pytest"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_sessions"] == 2
