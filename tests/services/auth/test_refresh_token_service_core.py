import types

import pytest

pytestmark = pytest.mark.unit


class DB:
    def __init__(self, user=None, token=None):
        self._user = user
        self._token = token

    async def execute(self, *args, **kwargs):
        class Result:
            def __init__(self, item):
                self._item = item

            def scalar_one_or_none(self):
                return self._item

        return Result(self._user)


@pytest.mark.asyncio
async def test_refresh_access_token_invalid_token_returns_none(monkeypatch):
    from app.services.auth import refresh_token as svc

    async def fake_verify(db, token):
        return None

    monkeypatch.setattr(svc, "verify_refresh_token_in_db", fake_verify)
    out = await svc.refresh_access_token(DB(), "raw")
    assert out is None


@pytest.mark.asyncio
async def test_refresh_access_token_deleted_user_returns_none(monkeypatch):
    from app.services.auth import refresh_token as svc

    async def fake_verify(db, token):
        return types.SimpleNamespace(user_id="uid")

    # DB returns deleted user
    db = DB(user=types.SimpleNamespace(id="uid", is_deleted=True))
    monkeypatch.setattr(svc, "verify_refresh_token_in_db", fake_verify)
    out = await svc.refresh_access_token(db, "raw")
    assert out is None


@pytest.mark.asyncio
async def test_revoke_session_missing_token_returns_false(monkeypatch):
    from app.services.auth import refresh_token as svc

    async def fake_verify(db, token):
        return None

    monkeypatch.setattr(svc, "verify_refresh_token_in_db", fake_verify)
    ok = await svc.revoke_session(DB(), "raw")
    assert ok is False


