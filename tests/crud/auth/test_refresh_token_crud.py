import types
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest


def _now():
    return datetime.now(timezone.utc)


class FakeToken:
    def __init__(
        self,
        user_id: str,
        created_at: datetime | None = None,
        expires_in_days: int = 30,
    ):
        self.id = UUID("00000000-0000-0000-0000-0000000000aa")
        self.user_id = user_id
        self.token_hash = "HASH"
        self.token_fingerprint = "FP"
        self.created_at = created_at or _now()
        self.expires_at = self.created_at + timedelta(days=expires_in_days)
        self.is_revoked = False


@pytest.mark.asyncio
async def test_create_refresh_token_commits_and_sets_fields(monkeypatch):
    from app.crud.auth import refresh_token as rt

    # Fake DB session
    calls = {"commit": 0, "add": 0, "refresh": 0}

    class DB:
        def add(self, obj):
            calls["add"] += 1

        async def commit(self):
            calls["commit"] += 1

        async def refresh(self, obj):
            calls["refresh"] += 1

    monkeypatch.setattr(rt, "utc_now", lambda: _now())
    token = await rt.create_refresh_token(
        DB(), "u1", "rawtoken", device_info="pytest", ip_address="127.0.0.1",
    )
    assert calls["add"] == 1 and calls["commit"] == 1
    assert token.user_id == "u1"
    assert token.device_info == "pytest"
    assert token.ip_address == "127.0.0.1"


@pytest.mark.asyncio
async def test_cleanup_expired_tokens_marks_revoked(monkeypatch):
    from app.crud.auth import refresh_token as rt

    tok_old = FakeToken(
        "u1", created_at=_now() - timedelta(days=40), expires_in_days=30,
    )
    tok_new = FakeToken("u1", created_at=_now(), expires_in_days=30)

    class Result:
        def scalars(self):
            return types.SimpleNamespace(all=lambda: [tok_old])

    class DB:
        async def execute(self, *a, **k):
            return Result()

        async def commit(self):
            pass

    monkeypatch.setattr(rt, "utc_now", lambda: _now())
    count = await rt.cleanup_expired_tokens(DB())
    assert count == 1
    assert tok_old.is_revoked is True


@pytest.mark.asyncio
async def test_revoke_refresh_token_by_id_and_hash(monkeypatch):
    from app.crud.auth import refresh_token as rt

    tok = FakeToken("u1")

    class Result:
        def __init__(self, token):
            self._t = token

        def scalar_one_or_none(self):
            return self._t

    class DB:
        def __init__(self, token):
            self.token = token

        async def execute(self, *a, **k):
            return Result(self.token)

        async def commit(self):
            pass

    # by id
    ok = await rt.revoke_refresh_token_by_id(DB(tok), str(tok.id))
    assert ok is True and tok.is_revoked is True

    # by hash path delegates; simulate found/not found
    async def fake_get_by_hash(db, h):
        return FakeToken("u1")

    monkeypatch.setattr(rt, "get_refresh_token_by_hash", fake_get_by_hash)
    ok2 = await rt.revoke_refresh_token(DB(None), "HASH")
    assert ok2 is True


@pytest.mark.asyncio
async def test_get_user_sessions_and_count(monkeypatch):
    from app.crud.auth import refresh_token as rt

    tok1 = FakeToken("u1")
    tok2 = FakeToken("u1")

    class Result:
        def scalars(self):
            return types.SimpleNamespace(all=lambda: [tok1, tok2])

    class DB:
        async def execute(self, *a, **k):
            return Result()

    monkeypatch.setattr(rt, "utc_now", lambda: _now())
    sessions = await rt.get_user_sessions(DB(), "u1")
    assert len(sessions) == 2
    assert await rt.get_user_session_count(DB(), "u1") == 2


@pytest.mark.asyncio
async def test_revoke_all_user_sessions(monkeypatch):
    from app.crud.auth import refresh_token as rt

    tok1 = FakeToken("u1")
    tok2 = FakeToken("u1")

    class Result:
        def scalars(self):
            return types.SimpleNamespace(all=lambda: [tok1, tok2])

    class DB:
        async def execute(self, *a, **k):
            return Result()

        async def commit(self):
            pass

    revoked = await rt.revoke_all_user_sessions(DB(), "u1")
    assert revoked == 2 and tok1.is_revoked and tok2.is_revoked


@pytest.mark.asyncio
async def test_enforce_session_limit_revokes_oldest(monkeypatch):
    from app.crud.auth import refresh_token as rt

    base = _now()
    newer = FakeToken("u1", created_at=base + timedelta(seconds=10))
    older = FakeToken("u1", created_at=base)

    class Result:
        def scalars(self):
            return types.SimpleNamespace(all=lambda: [older, newer])

    class DB:
        async def execute(self, *a, **k):
            return Result()

        async def commit(self):
            pass

    monkeypatch.setattr(rt, "utc_now", lambda: base)
    await rt.enforce_session_limit(DB(), "u1", max_sessions=1)
    assert older.is_revoked is True and newer.is_revoked is False
