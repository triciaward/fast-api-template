import types
import uuid

import pytest

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_create_user_session_sets_device_ip_and_enforces_limit(monkeypatch):
    from app.services.auth import refresh_token as rt

    user = types.SimpleNamespace(id=str(uuid.uuid4()))

    # Fake request
    request = types.SimpleNamespace(
        headers={"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X) Chrome"},
        client=types.SimpleNamespace(host="10.0.0.2"),
    )

    # Capture args passed to CRUD and session limit
    calls = {"create": None, "limit": None}

    async def fake_crud_create(db, user_id, token_hash, device_info, ip_address):
        calls["create"] = {
            "user_id": user_id,
            "token_hash": token_hash,
            "device_info": device_info,
            "ip_address": ip_address,
        }

    async def fake_enforce_limit(db, user_id, max_sessions):
        calls["limit"] = {"user_id": user_id, "max": max_sessions}

    # Make tokens deterministic
    monkeypatch.setattr(rt, "create_refresh_token_value", lambda: "rawtoken")
    monkeypatch.setattr(
        rt, "create_access_token", lambda subject, expires_delta: "accesstoken",
    )
    monkeypatch.setattr(rt, "crud_create_refresh_token", fake_crud_create)
    monkeypatch.setattr(rt, "enforce_session_limit", fake_enforce_limit)

    access, refresh = await rt.create_user_session(
        db=object(), user=user, request=request,
    )
    assert access == "accesstoken"
    assert refresh == "rawtoken"
    assert calls["create"]["device_info"].startswith("Chrome on ")
    assert calls["create"]["ip_address"] == "10.0.0.2"
    assert calls["limit"]["user_id"] == user.id


@pytest.mark.asyncio
async def test_refresh_access_token_invalid_token_returns_none(monkeypatch):
    from app.services.auth import refresh_token as rt

    async def fake_verify(db, token):
        return None

    monkeypatch.setattr(rt, "verify_refresh_token_in_db", fake_verify)
    result = await rt.refresh_access_token(db=object(), refresh_token_value="bad")
    assert result is None


@pytest.mark.asyncio
async def test_refresh_access_token_user_deleted_returns_none(monkeypatch):
    from app.services.auth import refresh_token as rt

    Token = types.SimpleNamespace

    async def fake_verify(db, token):
        return Token(user_id="u1")

    class Result:
        def __init__(self, user):
            self._user = user

        def scalar_one_or_none(self):  # type: ignore[no-untyped-def]
            return self._user

    async def fake_execute(stmt):  # type: ignore[no-untyped-def]
        return Result(types.SimpleNamespace(id="u1", is_deleted=True))

    monkeypatch.setattr(rt, "verify_refresh_token_in_db", fake_verify)
    # Patch select flow by monkeypatching the execute on the db session
    db = types.SimpleNamespace(execute=fake_execute)
    result = await rt.refresh_access_token(db=db, refresh_token_value="x")
    assert result is None


@pytest.mark.asyncio
async def test_revoke_session_success_and_not_found(monkeypatch):
    from app.services.auth import refresh_token as rt

    Token = types.SimpleNamespace

    async def fake_verify_ok(db, token):
        return Token(id="tid", user_id="u1")

    async def fake_verify_none(db, token):
        return None

    async def fake_revoke_by_id(db, token_id):
        return True

    monkeypatch.setattr(rt, "verify_refresh_token_in_db", fake_verify_ok)
    # Patch the CRUD function where revoke_session imports it from
    monkeypatch.setattr(
        "app.crud.auth.refresh_token.revoke_refresh_token_by_id",
        fake_revoke_by_id,
        raising=True,
    )
    assert await rt.revoke_session(db=object(), refresh_token_value="good") is True

    monkeypatch.setattr(rt, "verify_refresh_token_in_db", fake_verify_none)
    assert await rt.revoke_session(db=object(), refresh_token_value="bad") is False


@pytest.mark.asyncio
async def test_revoke_all_sessions_calls_crud_with_user(monkeypatch):
    from app.services.auth import refresh_token as rt

    calls = {"revoke_all": None}

    async def fake_revoke_all(db, user_id):
        calls["revoke_all"] = user_id
        return 3

    # hash lookup path if except_token provided (no-op for return)
    # Patch the CRUD function used inside revoke_all_sessions
    monkeypatch.setattr(
        "app.crud.revoke_all_user_sessions", fake_revoke_all, raising=True,
    )
    count = await rt.revoke_all_sessions(
        db=object(), user_id=uuid.uuid4(), except_token_value=None,
    )
    assert count == 3
    assert isinstance(calls["revoke_all"], str)
