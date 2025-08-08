import types

import pytest

pytestmark = pytest.mark.unit


class FakeResult:
    def __init__(self, value=None, many=None):
        self._value = value
        self._many = many or []

    def scalar_one_or_none(self):  # type: ignore[no-untyped-def]
        return self._value

    def scalars(self):  # type: ignore[no-untyped-def]
        return types.SimpleNamespace(all=lambda: self._many)


class FakeDB:
    def __init__(self, value=None, many=None):
        self.value = value
        self.many = many

    async def execute(self, _):  # type: ignore[no-untyped-def]
        return FakeResult(self.value, self.many)


def _user(i: int, **over):
    base = dict(id=str(i), email=f"u{i}@e.com", username=f"u{i}", is_deleted=False)
    base.update(over)
    return types.SimpleNamespace(**base)


@pytest.mark.asyncio
async def test_get_users_lists_and_count():
    from app.crud.auth import user as crud

    users = [_user(1), _user(2)]
    db = FakeDB(many=users)
    res = await crud.get_users(db, 0, 100)
    assert len(res) == 2

    db = FakeDB(many=users)
    n = await crud.count_users(db)
    assert n == 2


@pytest.mark.asyncio
async def test_get_deleted_users_and_count_deleted():
    from app.crud.auth import user as crud

    dels = [_user(3, is_deleted=True), _user(4, is_deleted=True)]
    db = FakeDB(many=dels)
    res = await crud.get_deleted_users(db, 0, 100)
    assert len(res) == 2

    db = FakeDB(many=dels)
    n = await crud.count_deleted_users(db)
    assert n == 2

