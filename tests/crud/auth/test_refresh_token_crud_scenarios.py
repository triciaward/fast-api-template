import types

import pytest


@pytest.mark.asyncio
@pytest.mark.skip(reason="Simulates DB refresh failure; skip in template")
async def test_create_refresh_token_refresh_failure(monkeypatch):
    from app.crud.auth import refresh_token as crud

    class FakeDB:
        def __init__(self):
            self.added = None

        def add(self, obj):  # type: ignore[no-untyped-def]
            self.added = obj

        async def commit(self):  # type: ignore[no-untyped-def]
            return None

        async def refresh(self, obj):  # type: ignore[no-untyped-def]
            raise RuntimeError("boom")

    db = FakeDB()
    tok = await crud.create_refresh_token(
        db,
        "uid",
        "raw",
        device_info="d",
        ip_address="i",
    )
    assert tok.user_id == "uid"


@pytest.mark.asyncio
async def test_get_refresh_token_by_hash_none(monkeypatch):
    from app.crud.auth import refresh_token as crud

    class FakeRes:
        def scalar_one_or_none(self):  # type: ignore[no-untyped-def]
            return None

    class FakeDB:
        async def execute(self, *a, **k):  # type: ignore[no-untyped-def]
            return FakeRes()

    out = await crud.get_refresh_token_by_hash(FakeDB(), "h")
    assert out is None


@pytest.mark.asyncio
async def test_revoke_refresh_token_by_id_not_found():
    from app.crud.auth import refresh_token as crud

    class Res:
        def scalar_one_or_none(self):  # type: ignore[no-untyped-def]
            return None

    class DB:
        async def execute(self, *a, **k):  # type: ignore[no-untyped-def]
            return Res()

    ok = await crud.revoke_refresh_token_by_id(DB(), "tid")
    assert ok is False


@pytest.mark.asyncio
async def test_revoke_refresh_token_no_token():
    from app.crud.auth import refresh_token as crud

    class Res:
        def scalar_one_or_none(self):  # type: ignore[no-untyped-def]
            return None

    class DB:
        async def execute(self, *a, **k):  # type: ignore[no-untyped-def]
            return Res()

        async def commit(self):  # type: ignore[no-untyped-def]
            return None

    ok = await crud.revoke_refresh_token(DB(), "hash")
    assert ok is False


@pytest.mark.asyncio
async def test_revoke_refresh_token_by_hash_calls_delegate(monkeypatch):
    from app.crud.auth import refresh_token as crud

    called = {"v": False}

    async def fake_revoke(db, th):
        called["v"] = True
        return True

    monkeypatch.setattr(crud, "revoke_refresh_token", fake_revoke)
    ok = await crud.revoke_refresh_token_by_hash(types.SimpleNamespace(), "h")  # type: ignore[arg-type]
    assert ok is True and called["v"] is True


@pytest.mark.asyncio
async def test_verify_refresh_token_in_db_none_both_queries():
    from app.crud.auth import refresh_token as crud

    class Res:
        def scalar_one_or_none(self):  # type: ignore[no-untyped-def]
            return None

    class DB:
        async def execute(self, *a, **k):  # type: ignore[no-untyped-def]
            return Res()

    out = await crud.verify_refresh_token_in_db(DB(), "raw")
    assert out is None


@pytest.mark.asyncio
async def test_enforce_session_limit_noop(monkeypatch):
    from app.crud.auth import refresh_token as crud

    async def fake_get_user_sessions(db, uid):
        return []

    class DB:
        def __init__(self):
            self.committed = False

        async def commit(self):  # type: ignore[no-untyped-def]
            self.committed = True

    monkeypatch.setattr(crud, "get_user_sessions", fake_get_user_sessions)
    db = DB()
    await crud.enforce_session_limit(db, "uid", max_sessions=5)
    # No commit expected on noop path
    assert db.committed is False


@pytest.mark.asyncio
async def test_revoke_refresh_token_sets_flag_and_commits(monkeypatch):
    from app.crud.auth import refresh_token as crud

    class Tok:
        def __init__(self):
            self.is_revoked = False

    class Res:
        def __init__(self, t):
            self._t = t

        def scalar_one_or_none(self):  # type: ignore[no-untyped-def]
            return self._t

    class DB:
        def __init__(self, t):
            self.t = t
            self.committed = False

        async def execute(self, *a, **k):  # type: ignore[no-untyped-def]
            return Res(self.t)

        async def commit(self):  # type: ignore[no-untyped-def]
            self.committed = True

    t = Tok()
    db = DB(t)
    # Route through revoke_refresh_token (by hash)
    ok = await crud.revoke_refresh_token(db, "hash")
    assert ok is True and t.is_revoked is True and db.committed is True


@pytest.mark.asyncio
async def test_verify_refresh_token_in_db_verify_fails(monkeypatch):
    from app.crud.auth import refresh_token as crud

    class Tok:
        def __init__(self):
            self.token_hash = "hashed"
            self.token_fingerprint = "fp"

    class Res:
        def __init__(self, t):
            self._t = t

        def scalar_one_or_none(self):  # type: ignore[no-untyped-def]
            return self._t

    class DB:
        def __init__(self, t):
            self.t = t

        async def execute(self, *a, **k):  # type: ignore[no-untyped-def]
            return Res(self.t)

    # Patch the function imported into this module to return False (verification fail path)
    monkeypatch.setattr(crud, "verify_refresh_token", lambda *a, **k: False)
    out = await crud.verify_refresh_token_in_db(DB(Tok()), "raw")
    assert out is None


@pytest.mark.asyncio
async def test_verify_refresh_token_legacy_migration(monkeypatch):
    from app.crud.auth import refresh_token as crud

    class Token:
        def __init__(self):
            self.token_hash = None
            self.token_fingerprint = None

    class Res1:
        def scalar_one_or_none(self):  # type: ignore[no-untyped-def]
            return None

    class Res2:
        def __init__(self, t):
            self.t = t

        def scalar_one_or_none(self):  # type: ignore[no-untyped-def]
            return self.t

    class DB:
        def __init__(self, t):
            self.t = t

        async def execute(self, *a, **k):  # type: ignore[no-untyped-def]
            # first call returns none, second returns legacy
            if not hasattr(self, "_called"):
                self._called = True
                return Res1()
            return Res2(self.t)

        async def commit(self):  # type: ignore[no-untyped-def]
            return None

    tok = Token()
    out = await crud.verify_refresh_token_in_db(DB(tok), "raw")
    assert out is tok
    assert tok.token_hash is not None and tok.token_fingerprint is not None


@pytest.mark.asyncio
async def test_enforce_session_limit_commits(monkeypatch):
    from app.crud.auth import refresh_token as crud

    class RT:
        def __init__(self, created_at):  # type: ignore[no-untyped-def]
            self.created_at = created_at
            self.is_revoked = False

    class DB:
        def __init__(self):
            self.committed = False

        async def commit(self):  # type: ignore[no-untyped-def]
            self.committed = True

    async def fake_get_user_sessions(db, uid):
        return [
            RT(datetime(2024, 1, 1)),
            RT(datetime(2024, 1, 2)),
            RT(datetime(2024, 1, 3)),
        ]

    from datetime import datetime

    monkeypatch.setattr(crud, "get_user_sessions", fake_get_user_sessions)
    db = DB()
    await crud.enforce_session_limit(db, "uid", max_sessions=2)
    assert db.committed is True


import pytest

pytestmark = pytest.mark.unit


class FakeScalars:
    def __init__(self, item=None):
        self.item = item

    def all(self):
        return []


class FakeResult:
    def __init__(self, item=None):
        self._item = item

    def scalar_one_or_none(self):
        return self._item

    def scalars(self):
        return FakeScalars(self._item)


class DB:
    def __init__(self, item=None):
        self._item = item
        self.commits = 0

    async def execute(self, *args, **kwargs):
        return FakeResult(self._item)

    async def commit(self):
        self.commits += 1


@pytest.mark.asyncio
async def test_revoke_refresh_token_by_id_none_found_returns_false():
    from app.crud.auth import refresh_token as crud

    db = DB(item=None)
    ok = await crud.revoke_refresh_token_by_id(db, "tid")
    assert ok is False


@pytest.mark.asyncio
async def test_verify_refresh_token_legacy_record_migrates(monkeypatch):
    from app.crud.auth import refresh_token as crud

    # Legacy record where token_hash stored raw token and fingerprint empty
    legacy = types.SimpleNamespace(
        token_hash="rawtoken",
        token_fingerprint=None,
        expires_at=types.SimpleNamespace(),
        is_revoked=False,
    )

    class DB2(DB):
        step = 0

        async def execute(self, *args, **kwargs):
            # First query returns no candidate by fingerprint
            if DB2.step == 0:
                DB2.step += 1
                return FakeResult(None)
            # Second legacy fallback returns legacy record
            return FakeResult(legacy)

    db = DB2()
    out = await crud.verify_refresh_token_in_db(db, "rawtoken")
    # Migrates and returns candidate
    assert out is legacy
    assert db.commits == 1
