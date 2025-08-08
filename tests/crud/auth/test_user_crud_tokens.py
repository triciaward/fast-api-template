import types

import pytest

pytestmark = pytest.mark.unit


class FakeResult:
    def __init__(self, value=None):
        self._value = value

    def scalar_one_or_none(self):  # type: ignore[no-untyped-def]
        return self._value


class FakeDB:
    def __init__(self, value=None):
        self.value = value
        self.commit_called = 0

    async def execute(self, _):  # type: ignore[no-untyped-def]
        return FakeResult(self.value)

    async def commit(self):  # type: ignore[no-untyped-def]
        self.commit_called += 1


def _user(**over):
    base = dict(
        id="u1",
        email="u@example.com",
        username="u",
        is_deleted=False,
        is_verified=False,
    )
    base.update(over)
    return types.SimpleNamespace(**base)


@pytest.mark.asyncio
async def test_update_verification_token_none_and_success():
    from app.crud.auth import user as crud

    db = FakeDB(value=None)
    ok = await crud.update_verification_token(db, "u1", "tok", types.SimpleNamespace())
    assert ok is False

    db = FakeDB(value=_user())
    ok = await crud.update_verification_token(db, "u1", "tok", types.SimpleNamespace())
    assert ok is True and db.commit_called >= 1


@pytest.mark.asyncio
async def test_update_password_reset_token_none_and_success():
    from app.crud.auth import user as crud

    db = FakeDB(value=None)
    ok = await crud.update_password_reset_token(db, "u1", "tok", types.SimpleNamespace())
    assert ok is False

    db = FakeDB(value=_user())
    ok = await crud.update_password_reset_token(db, "u1", "tok", types.SimpleNamespace())
    assert ok is True and db.commit_called >= 1


@pytest.mark.asyncio
async def test_update_deletion_token_none_and_success():
    from app.crud.auth import user as crud

    db = FakeDB(value=None)
    ok = await crud.update_deletion_token(db, "u1", "tok", types.SimpleNamespace())
    assert ok is False

    db = FakeDB(value=_user())
    ok = await crud.update_deletion_token(db, "u1", "tok", types.SimpleNamespace())
    assert ok is True and db.commit_called >= 1


@pytest.mark.asyncio
async def test_verify_user_none_and_success():
    from app.crud.auth import user as crud

    db = FakeDB(value=None)
    ok = await crud.verify_user(db, "u1")
    assert ok is False

    db = FakeDB(value=_user())
    ok = await crud.verify_user(db, "u1")
    assert ok is True and db.commit_called >= 1


@pytest.mark.asyncio
async def test_schedule_confirm_cancel_deletion_none_and_success():
    from app.crud.auth import user as crud

    # schedule
    db = FakeDB(value=None)
    ok = await crud.schedule_user_deletion(db, "u1", types.SimpleNamespace())
    assert ok is False

    db = FakeDB(value=_user())
    ok = await crud.schedule_user_deletion(db, "u1", types.SimpleNamespace())
    assert ok is True

    # confirm
    db = FakeDB(value=None)
    ok = await crud.confirm_user_deletion(db, "u1")
    assert ok is False

    db = FakeDB(value=_user())
    ok = await crud.confirm_user_deletion(db, "u1")
    assert ok is True

    # cancel
    db = FakeDB(value=None)
    ok = await crud.cancel_user_deletion(db, "u1")
    assert ok is False

    db = FakeDB(value=_user())
    ok = await crud.cancel_user_deletion(db, "u1")
    assert ok is True

