import types
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from starlette.requests import Request

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_get_current_user_success_and_invalid(monkeypatch):
    from app.api.users import auth as mod

    # Success path: jwt.decode returns payload with sub
    monkeypatch.setattr(
        mod.jwt, "decode", lambda token, key, algorithms: {"sub": "user-1"}
    )

    async def get_user_by_id(db, user_id):
        return types.SimpleNamespace(id=user_id, is_superuser=False)

    monkeypatch.setattr(mod.crud_user, "get_user_by_id", get_user_by_id)

    user = await mod.get_current_user(token="tok", db=types.SimpleNamespace())
    assert user.id == "user-1"

    # Invalid token: jwt raises
    class FakeJWTError(Exception):
        pass

    def decode_raises(*a, **k):
        raise mod.JWTError("bad")

    monkeypatch.setattr(mod.jwt, "decode", decode_raises)

    with pytest.raises(Exception) as exc:
        await mod.get_current_user(token="bad", db=types.SimpleNamespace())
    assert "Could not validate credentials" in str(exc.value)


def _request() -> Request:
    return Request(scope={"type": "http", "method": "GET", "path": "/"})


@pytest.mark.asyncio
async def test_get_api_key_user_header_errors(monkeypatch):
    from app.api.users import auth as mod

    # Missing header
    with pytest.raises(Exception) as exc1:
        await mod.get_api_key_user(
            request=_request(), authorization=None, db=types.SimpleNamespace()
        )
    assert "API key required" in str(exc1.value)

    # Bad format
    with pytest.raises(Exception) as exc2:
        await mod.get_api_key_user(
            request=_request(), authorization="Token abc", db=types.SimpleNamespace()
        )
    assert "Invalid authorization header format" in str(exc2.value)


@pytest.mark.asyncio
async def test_get_api_key_user_invalid_inactive_expired(monkeypatch):
    from app.api.users import auth as mod

    # verify_api_key_in_db returns None
    async def verify_none(db, api_key):
        return None

    monkeypatch.setattr(mod.crud_api_key, "verify_api_key_in_db", verify_none)

    with pytest.raises(Exception) as exc:
        await mod.get_api_key_user(
            request=_request(), authorization="Bearer key", db=types.SimpleNamespace()
        )
    assert "Invalid API key" in str(exc.value)

    # inactive
    async def verify_inactive(db, api_key):
        return types.SimpleNamespace(is_active=False)

    monkeypatch.setattr(mod.crud_api_key, "verify_api_key_in_db", verify_inactive)

    with pytest.raises(Exception) as exc2:
        await mod.get_api_key_user(
            request=_request(), authorization="Bearer key", db=types.SimpleNamespace()
        )
    assert "inactive" in str(exc2.value)

    # expired
    exp = datetime.now(timezone.utc) - timedelta(days=1)

    async def verify_expired(db, api_key):
        return types.SimpleNamespace(is_active=True, expires_at=exp)

    monkeypatch.setattr(mod.crud_api_key, "verify_api_key_in_db", verify_expired)
    monkeypatch.setattr(mod, "utc_now", lambda: datetime.now(timezone.utc))

    with pytest.raises(Exception) as exc3:
        await mod.get_api_key_user(
            request=_request(), authorization="Bearer key", db=types.SimpleNamespace()
        )
    assert "has expired" in str(exc3.value)


@pytest.mark.asyncio
async def test_get_api_key_user_success_and_scope_check(monkeypatch):
    from app.api.users import auth as mod

    # valid key
    async def verify_ok(db, api_key):
        return types.SimpleNamespace(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            is_active=True,
            expires_at=None,
            scopes=["read", "write"],
            label="my key",
        )

    async def log_api_key_usage(**kwargs):
        return None

    async def log_wrapper(*a, **k):
        return await log_api_key_usage(**k)

    monkeypatch.setattr(mod.crud_api_key, "verify_api_key_in_db", verify_ok)
    # Patch audit logger import target
    from app.services.monitoring import audit as audit_mod

    monkeypatch.setattr(audit_mod, "log_api_key_usage", log_api_key_usage)

    api_user = await mod.get_api_key_user(
        request=_request(), authorization="Bearer good", db=types.SimpleNamespace()
    )
    assert api_user.key_id is not None and "read" in api_user.scopes

    # require_api_scope
    dep = mod.require_api_scope("write")
    # Call dependency directly with the api_user
    assert dep(api_user) is api_user

    # missing scope should raise
    dep2 = mod.require_api_scope("admin")
    with pytest.raises(Exception) as exc:
        dep2(api_user)
    assert "missing required scope" in str(exc.value)
