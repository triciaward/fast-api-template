import types
from datetime import datetime, timezone
from uuid import UUID

import pytest


def _now():
    return datetime.now(timezone.utc)


def _user():
    return types.SimpleNamespace(
        id=UUID("00000000-0000-0000-0000-0000000000ab"),
        email="user@example.com",
        username="validuser",
        is_superuser=False,
        is_verified=True,
        is_deleted=False,
        created_at=_now(),
        oauth_provider=None,
    )


class FakeToken:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.id = UUID("00000000-0000-0000-0000-0000000000ff")


@pytest.mark.asyncio
async def test_refresh_token_no_cookie(monkeypatch, async_client):
    from app.services.auth import refresh_token as rt_svc

    monkeypatch.setattr(rt_svc, "get_refresh_token_from_cookie", lambda req: None)

    resp = await async_client.post("/auth/refresh", headers={"user-agent": "pytest"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_success(monkeypatch, async_client):
    from app.services.auth import refresh_token as rt_svc

    monkeypatch.setattr(rt_svc, "get_refresh_token_from_cookie", lambda req: "rtok")

    async def fake_refresh_access_token(db, value):
        return ("new_access", _now())

    monkeypatch.setattr(rt_svc, "refresh_access_token", fake_refresh_access_token)

    resp = await async_client.post("/auth/refresh", headers={"user-agent": "pytest"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"] == "new_access"
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_token_invalid_token(monkeypatch, async_client):
    from app.services.auth import refresh_token as rt_svc

    monkeypatch.setattr(rt_svc, "get_refresh_token_from_cookie", lambda req: "rtok")

    async def fake_refresh_access_token(db, value):
        return None

    monkeypatch.setattr(rt_svc, "refresh_access_token", fake_refresh_access_token)

    resp = await async_client.post("/auth/refresh", headers={"user-agent": "pytest"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_logout_no_cookie(monkeypatch, async_client):
    from app.services.auth import refresh_token as rt_svc

    monkeypatch.setattr(rt_svc, "get_refresh_token_from_cookie", lambda req: None)
    monkeypatch.setattr(rt_svc, "clear_refresh_token_cookie", lambda resp: None)

    resp = await async_client.post("/auth/logout", headers={"user-agent": "pytest"})
    assert resp.status_code == 200
    assert resp.json()["message"].startswith("Successfully logged out")


@pytest.mark.asyncio
async def test_logout_clears_cookie_and_revokes(monkeypatch, async_client):
    from app import crud
    from app.api.auth import session_management as sm
    from app.crud.auth import user as crud_user
    from app.services.auth import refresh_token as rt_svc

    monkeypatch.setattr(rt_svc, "get_refresh_token_from_cookie", lambda req: "rtok")
    monkeypatch.setattr(rt_svc, "clear_refresh_token_cookie", lambda resp: None)

    async def fake_verify(db, tok):
        return FakeToken(user_id=str(_user().id))

    async def fake_get_user_by_id(db, uid):
        return _user()

    async def fake_revoke(db, tok):
        return None

    async def fake_log(*a, **k):
        return None

    monkeypatch.setattr(crud, "verify_refresh_token_in_db", fake_verify)
    monkeypatch.setattr(crud_user, "get_user_by_id", fake_get_user_by_id)
    monkeypatch.setattr(rt_svc, "revoke_session", fake_revoke)
    monkeypatch.setattr(sm, "log_logout", fake_log)

    resp = await async_client.post("/auth/logout", headers={"user-agent": "pytest"})
    assert resp.status_code == 200
    assert resp.json()["message"].startswith("Successfully logged out")


@pytest.mark.asyncio
async def test_get_sessions_success(monkeypatch, async_client):
    from app import crud
    from app.crud.auth import refresh_token as rt_crud
    from app.services.auth import refresh_token as rt_svc

    # Ensure current session cookie present to follow code path
    monkeypatch.setattr(rt_svc, "get_refresh_token_from_cookie", lambda req: "rtok")

    class Sess:
        def __init__(self):
            self.id = UUID("00000000-0000-0000-0000-0000000000aa")
            self.created_at = _now()
            self.device_info = "pytest"
            self.ip_address = "127.0.0.1"
            self.is_current = True

    async def fake_get_user_sessions(db, user_id):
        return [Sess()]

    monkeypatch.setattr(rt_crud, "get_user_sessions", fake_get_user_sessions)

    async def fake_verify(db, tok):
        return FakeToken(user_id=str(_user().id))

    monkeypatch.setattr(crud, "verify_refresh_token_in_db", fake_verify)

    # Mock auth dependency
    from app.api.users import auth as users_auth
    from app.main import app

    app.dependency_overrides[users_auth.get_current_user] = lambda: _user()
    try:
        resp = await async_client.get(
            "/auth/sessions",
            headers={"user-agent": "pytest"},
        )
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_sessions"] == 1
    assert data["sessions"][0]["is_current"] is True


@pytest.mark.asyncio
async def test_revoke_session_invalid_id(monkeypatch, async_client):
    from app.api.users import auth as users_auth
    from app.main import app

    app.dependency_overrides[users_auth.get_current_user] = lambda: _user()
    try:
        resp = await async_client.delete(
            "/auth/sessions/not-a-uuid",
            headers={"user-agent": "pytest"},
        )
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_revoke_session_not_found(monkeypatch, async_client):
    from app.api.users import auth as users_auth
    from app.crud.auth import refresh_token as rt_crud
    from app.main import app

    app.dependency_overrides[users_auth.get_current_user] = lambda: _user()

    async def fake_revoke_by_id(db, sid):
        return False

    monkeypatch.setattr(rt_crud, "revoke_refresh_token_by_id", fake_revoke_by_id)

    try:
        resp = await async_client.delete(
            "/auth/sessions/00000000-0000-0000-0000-0000000000bb",
            headers={"user-agent": "pytest"},
        )
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_revoke_session_success(monkeypatch, async_client):
    from app.api.users import auth as users_auth
    from app.crud.auth import refresh_token as rt_crud
    from app.main import app

    app.dependency_overrides[users_auth.get_current_user] = lambda: _user()

    async def fake_revoke_by_id(db, sid):
        return True

    monkeypatch.setattr(rt_crud, "revoke_refresh_token_by_id", fake_revoke_by_id)

    try:
        resp = await async_client.delete(
            "/auth/sessions/00000000-0000-0000-0000-0000000000bb",
            headers={"user-agent": "pytest"},
        )
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert resp.json()["message"] == "Session revoked successfully"


@pytest.mark.asyncio
async def test_revoke_all_sessions_success(monkeypatch, async_client):
    from app.api.auth import session_management as sm
    from app.api.users import auth as users_auth
    from app.crud.auth import refresh_token as rt_crud
    from app.crud.auth import user as crud_user
    from app.main import app

    app.dependency_overrides[users_auth.get_current_user] = lambda: _user()

    async def fake_get_user_by_id(db, uid):
        return _user()

    async def fake_revoke_all(db, uid):
        return 2

    async def fake_log(*a, **k):
        return None

    monkeypatch.setattr(crud_user, "get_user_by_id", fake_get_user_by_id)
    monkeypatch.setattr(rt_crud, "revoke_all_user_sessions", fake_revoke_all)
    monkeypatch.setattr(sm, "log_logout", fake_log)

    try:
        resp = await async_client.delete(
            "/auth/sessions",
            headers={"user-agent": "pytest"},
        )
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert "All sessions revoked successfully" in resp.json()["message"]


@pytest.mark.asyncio
async def test_revoke_all_sessions_user_not_found(monkeypatch, async_client):
    from app.api.users import auth as users_auth
    from app.crud.auth import user as crud_user
    from app.main import app

    app.dependency_overrides[users_auth.get_current_user] = lambda: _user()

    async def fake_get_user_by_id(db, uid):
        return None

    monkeypatch.setattr(crud_user, "get_user_by_id", fake_get_user_by_id)

    try:
        resp = await async_client.delete(
            "/auth/sessions",
            headers={"user-agent": "pytest"},
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 500
    body = resp.json()
    assert "User not found" in body.get("error", {}).get("message", "")


@pytest.mark.asyncio
async def test_refresh_token_expires_in_calculation(monkeypatch, async_client):
    from datetime import timedelta

    from app.api.auth import session_management as sm
    from app.services.auth import refresh_token as rt_svc

    fixed_now = _now()
    monkeypatch.setattr(sm, "utc_now", lambda: fixed_now)
    monkeypatch.setattr(rt_svc, "get_refresh_token_from_cookie", lambda req: "rtok")

    async def fake_refresh_access_token(db, value):
        return ("tok", fixed_now + timedelta(seconds=42))

    monkeypatch.setattr(rt_svc, "refresh_access_token", fake_refresh_access_token)

    resp = await async_client.post("/auth/refresh", headers={"user-agent": "pytest"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["expires_in"] == 42


@pytest.mark.asyncio
async def test_get_sessions_multiple_with_is_current(monkeypatch, async_client):
    from app import crud
    from app.api.users import auth as users_auth
    from app.crud.auth import refresh_token as rt_crud
    from app.main import app

    app.dependency_overrides[users_auth.get_current_user] = lambda: _user()

    class Sess:
        def __init__(self, sid: str, is_current: bool):
            self.id = UUID(sid)
            self.created_at = _now()
            self.device_info = "pytest"
            self.ip_address = "127.0.0.1"
            self.is_current = is_current

    async def fake_get_user_sessions(db, user_id):
        return [
            Sess("00000000-0000-0000-0000-0000000000aa", False),
            Sess("00000000-0000-0000-0000-0000000000bb", True),
        ]

    async def fake_verify(db, tok):
        return FakeToken(user_id=str(_user().id))

    monkeypatch.setattr(rt_crud, "get_user_sessions", fake_get_user_sessions)
    monkeypatch.setattr(crud, "verify_refresh_token_in_db", fake_verify)

    from app.services.auth import refresh_token as rt_svc

    monkeypatch.setattr(rt_svc, "get_refresh_token_from_cookie", lambda req: "rtok")

    try:
        resp = await async_client.get(
            "/auth/sessions",
            headers={"user-agent": "pytest"},
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["total_sessions"] == 2
    assert data["sessions"][0]["is_current"] is False
    assert data["sessions"][1]["is_current"] is True
