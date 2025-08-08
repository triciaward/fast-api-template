import pytest

pytestmark = pytest.mark.unit


class FakeScalars:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


class FakeResult:
    def __init__(self, single=None, items=None):
        self._single = single
        self._items = [] if items is None else items

    def scalar_one_or_none(self):
        return self._single

    def scalars(self):
        return FakeScalars(self._items)


class FakeDB:
    def __init__(self):
        self.added = []
        self.deleted = []
        self.refreshed = []
        self.commits = 0
        self._result = FakeResult()

    async def execute(self, stmt):
        return self._result

    def set_result(self, single=None, items=None):
        self._result = FakeResult(single, items)

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.commits += 1

    async def refresh(self, obj):
        self.refreshed.append(obj)

    async def delete(self, obj):
        self.deleted.append(obj)


@pytest.mark.asyncio
async def test_get_user_by_username_none():
    from app.crud.auth import user as crud

    db = FakeDB()
    db.set_result(single=None)
    user = await crud.get_user_by_username(db, "nobody")
    assert user is None


@pytest.mark.asyncio
async def test_get_user_by_oauth_id_found_and_none():
    from app.crud.auth import user as crud
    from app.models import User

    db = FakeDB()
    # Found
    db.set_result(single=User(email="a@x.com", username="a"))
    u = await crud.get_user_by_oauth_id(db, "google", "gid")
    assert u is not None
    # None
    db.set_result(single=None)
    u2 = await crud.get_user_by_oauth_id(db, "google", "gid")
    assert u2 is None


@pytest.mark.asyncio
async def test_create_oauth_user_sets_verified_and_commits():
    from app.crud.auth import user as crud

    db = FakeDB()
    u = await crud.create_oauth_user(db, "b@x.com", "b", "google", "gid2", "b@x.com")
    assert u.is_verified is True
    assert db.commits == 1
    assert len(db.added) == 1


@pytest.mark.asyncio
async def test_get_user_by_verification_token_found_and_none():
    from app.crud.auth import user as crud
    from app.models import User

    db = FakeDB()
    db.set_result(single=User(email="c@x.com", username="c"))
    u = await crud.get_user_by_verification_token(db, "tok")
    assert u is not None
    db.set_result(single=None)
    u2 = await crud.get_user_by_verification_token(db, "tok")
    assert u2 is None


@pytest.mark.asyncio
async def test_get_user_by_deletion_token_found_and_none():
    from app.crud.auth import user as crud
    from app.models import User

    db = FakeDB()
    db.set_result(single=User(email="d@x.com", username="d"))
    u = await crud.get_user_by_deletion_token(db, "tok")
    assert u is not None
    db.set_result(single=None)
    u2 = await crud.get_user_by_deletion_token(db, "tok")
    assert u2 is None


@pytest.mark.asyncio
async def test_permanently_delete_user_found_and_none():
    from app.crud.auth import user as crud
    from app.models import User

    db = FakeDB()

    async def fake_get_any(db2, uid):
        return User(email="e@x.com", username="e")

    # Found
    result = await crud.permanently_delete_user(db, "id1") if False else None  # ensure import
    # Monkeypatch via attribute assignment since module-level function
    crud.get_user_by_id_any_status = fake_get_any  # type: ignore[assignment]
    ok = await crud.permanently_delete_user(db, "id1")
    assert ok is True
    assert len(db.deleted) == 1

    # None
    async def fake_none(db2, uid):
        return None

    crud.get_user_by_id_any_status = fake_none  # type: ignore[assignment]
    ok2 = await crud.permanently_delete_user(db, "id1")
    assert ok2 is False


@pytest.mark.asyncio
async def test_get_users_for_deletion_and_counts():
    from app.crud.auth import user as crud
    from app.models import User

    db = FakeDB()
    # Empty paths
    db.set_result(items=[])
    lst = await crud.get_users_for_deletion_reminder(db)
    assert lst == []
    lst2 = await crud.get_users_for_permanent_deletion(db)
    assert lst2 == []
    c1 = await crud.count_users(db)
    assert c1 == 0
    c2 = await crud.count_deleted_users(db)
    assert c2 == 0

    # Non-empty
    users = [User(email=f"u{i}@x.com", username=f"u{i}") for i in range(3)]
    db.set_result(items=users)
    lst = await crud.get_users_for_deletion_reminder(db)
    assert len(lst) == 3
    lst2 = await crud.get_users_for_permanent_deletion(db)
    assert len(lst2) == 3
    c1 = await crud.count_users(db)
    assert c1 == 3
    c2 = await crud.count_deleted_users(db)
    assert c2 == 3


