import types

import pytest

from app.crud.auth import api_key as crud
from app.schemas.auth.user import APIKeyCreate


class _ScalarOneOrNoneResult:
    def __init__(self, obj):  # type: ignore[no-untyped-def]
        self._obj = obj

    def scalar_one_or_none(self):  # type: ignore[no-untyped-def]
        return self._obj


class _ListScalarsResult:
    def __init__(self, items):  # type: ignore[no-untyped-def]
        self._items = items

    class _Scalars:
        def __init__(self, items):  # type: ignore[no-untyped-def]
            self._items = items

        def all(self):  # type: ignore[no-untyped-def]
            return self._items

    def scalars(self):  # type: ignore[no-untyped-def]
        return self._Scalars(self._items)


class _FakeSession:
    def __init__(self, result=None):  # type: ignore[no-untyped-def]
        self._result = result
        self.added = []
        self.committed = False

    async def execute(self, *_args, **_kwargs):  # type: ignore[no-untyped-def]
        return self._result

    def add(self, obj):  # type: ignore[no-untyped-def]
        self.added.append(obj)

    async def commit(self):  # type: ignore[no-untyped-def]
        self.committed = True

    async def refresh(self, obj):  # type: ignore[no-untyped-def]
        pass


pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_create_api_key_generates_and_hashes(monkeypatch):
    monkeypatch.setattr(crud, "generate_api_key", lambda: "RAW")
    monkeypatch.setattr(crud, "hash_api_key", lambda k: "HASH")
    monkeypatch.setattr(crud, "fingerprint_api_key", lambda k: "FP")

    db = _FakeSession()
    created = await crud.create_api_key(db, APIKeyCreate(label="l", scopes=["read"]))
    assert db.committed is True
    assert len(db.added) == 1
    assert created.key_hash == "HASH"


@pytest.mark.asyncio
async def test_verify_api_key_in_db_success(monkeypatch):
    db_key = types.SimpleNamespace(key_hash="HASH", is_active=True, expires_at=None)

    monkeypatch.setattr(crud, "fingerprint_api_key", lambda k: "FP")
    monkeypatch.setattr(crud, "verify_api_key", lambda raw, hashed: True)

    db = _FakeSession(_ScalarOneOrNoneResult(db_key))
    ok = await crud.verify_api_key_in_db(db, "RAW")
    assert ok is db_key


@pytest.mark.asyncio
async def test_deactivate_and_rotate(monkeypatch):
    key = types.SimpleNamespace(id="k1", is_active=True, user_id="u1", label="L", scopes=["read"], expires_at=None)

    async def fake_get_api_key_by_id(db, key_id, user_id=None):
        return key

    monkeypatch.setattr(crud, "get_api_key_by_id", fake_get_api_key_by_id)
    monkeypatch.setattr(crud, "generate_api_key", lambda: "NEWRAW")
    monkeypatch.setattr(crud, "hash_api_key", lambda v: "NEWHASH")

    class _DB(_FakeSession):
        async def delete(self, obj):  # type: ignore[no-untyped-def]
            pass

    db = _DB()

    # Deactivate
    ok = await crud.deactivate_api_key(db, "k1")
    assert ok is True and key.is_active is False

    # Rotate
    new_key, raw = await crud.rotate_api_key(db, "k1")
    assert raw == "NEWRAW"
    assert new_key.key_hash == "NEWHASH"


