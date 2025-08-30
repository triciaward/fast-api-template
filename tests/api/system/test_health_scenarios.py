import sys
import types

import pytest


@pytest.fixture(autouse=True)
async def _override_health_api_key_dependency():
    from uuid import uuid4

    from app.api.users import auth as auth_mod
    from app.main import app
    from app.schemas.auth.user import APIKeyUser

    async def fake_get_api_key_user():  # type: ignore[no-untyped-def]
        return APIKeyUser(
            id=uuid4(),
            scopes=["system:read"],
            user_id=None,
            key_id=uuid4(),
        )

    app.dependency_overrides[auth_mod.get_api_key_user] = fake_get_api_key_user
    try:
        yield
    finally:
        app.dependency_overrides.pop(auth_mod.get_api_key_user, None)


@pytest.mark.asyncio
async def test_health_check_db_pool_metrics_success(monkeypatch, async_client):
    # Mock DB execute to succeed
    class FakeResult:
        def fetchone(self):
            return (1,)

    async def fake_execute(query):  # type: ignore[no-untyped-def]
        return FakeResult()

    # Override dependency get_db by monkeypatching the call site via app.dependency_overrides
    from app.api.system import health as mod
    from app.main import app

    class FakeSession:
        async def execute(self, q):  # type: ignore[no-untyped-def]
            return await fake_execute(q)

    async def fake_get_db():  # type: ignore[no-untyped-def]
        yield FakeSession()

    app.dependency_overrides[mod.get_db] = fake_get_db

    # Provide engine.pool attributes
    class FakePool:
        def size(self):
            return 5

        def checkedin(self):
            return 3

        def checkedout(self):
            return 2

        def overflow(self):
            return 0

    class FakeEngine:
        pool = FakePool()

    fake_db_module = types.SimpleNamespace(engine=FakeEngine())
    monkeypatch.setitem(sys.modules, "app.database.database", fake_db_module)

    r = await async_client.get("/api/system/health")
    app.dependency_overrides.clear()
    assert r.status_code == 200
    data = r.json()
    assert data["checks"]["database"] == "healthy"
    assert "database_pools" in data and "async" in data["database_pools"]


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires engine import failure simulation; skip in template")
async def test_health_check_db_pool_metrics_failure(monkeypatch, async_client):
    # Mock DB execute to succeed
    class FakeResult:
        def fetchone(self):
            return (1,)

    async def fake_execute(query):  # type: ignore[no-untyped-def]
        return FakeResult()

    from app.api.system import health as mod
    from app.main import app

    class FakeSession:
        async def execute(self, q):  # type: ignore[no-untyped-def]
            return await fake_execute(q)

    async def fake_get_db():  # type: ignore[no-untyped-def]
        yield FakeSession()

    app.dependency_overrides[mod.get_db] = fake_get_db

    # Force engine import to raise when accessing pool metrics
    def boom_import(name, *args, **kwargs):  # type: ignore[no-untyped-def]
        if name == "app.database.database":
            raise RuntimeError("no engine")
        return original_import(name, *args, **kwargs)

    original_import = __import__
    monkeypatch.setattr("builtins.__import__", boom_import)  # type: ignore[arg-type]

    r = await async_client.get("/api/system/health")
    app.dependency_overrides.clear()
    # When pool metrics fail, endpoint raises 500
    assert r.status_code == 500
    body = r.json()
    assert body["error"]["code"] in {"internal_error", "invalid_request"}


@pytest.mark.asyncio
@pytest.mark.skip(
    reason="Requires DB unhealthy branch with complex query; skip in template",
)
async def test_database_health_endpoint_unhealthy(monkeypatch, async_client):
    # Make first execute succeed, second raise to test unhealthy branch
    call = {"n": 0}

    class FakeResult:
        def fetchone(self):
            return (1,)

    async def fake_execute(query):  # type: ignore[no-untyped-def]
        call["n"] += 1
        if call["n"] == 1:
            return FakeResult()
        raise RuntimeError("bad query")

    from app.api.system import health as mod
    from app.main import app

    class FakeSession:
        async def execute(self, q):  # type: ignore[no-untyped-def]
            return await fake_execute(q)

    async def fake_get_db():  # type: ignore[no-untyped-def]
        yield FakeSession()

    app.dependency_overrides[mod.get_db] = fake_get_db

    r = await async_client.get("/api/system/health/database")
    app.dependency_overrides.clear()
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "unhealthy"
    assert "error" in data
