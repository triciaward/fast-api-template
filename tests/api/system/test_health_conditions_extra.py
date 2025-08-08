import pytest


@pytest.mark.asyncio
async def test_health_simple_includes_redis_when_enabled(monkeypatch, async_client):
    from app.api.system import health as mod
    from app.core.config import settings
    from app.main import app

    monkeypatch.setattr(settings, "ENABLE_REDIS", True, raising=False)

    class FakeResult:
        def fetchone(self):
            return (1,)

    class FakeSession:
        async def execute(self, q):
            return FakeResult()

    async def fake_get_db():
        yield FakeSession()

    app.dependency_overrides[mod.get_db] = fake_get_db

    # Provide minimal engine.pool so pool metrics retrieval succeeds
    class FakePool:
        def size(self):
            return 1

        def checkedin(self):
            return 1

        def checkedout(self):
            return 0

        def overflow(self):
            return 0

    class FakeEngine:
        pool = FakePool()

    # Monkeypatch engine at import site
    import sys
    import types

    fake_db_module = types.SimpleNamespace(engine=FakeEngine())
    monkeypatch.setitem(sys.modules, "app.database.database", fake_db_module)

    r = await async_client.get("/system/health")
    app.dependency_overrides.clear()
    assert r.status_code == 200
    data = r.json()
    assert "redis" in data["checks"]


@pytest.mark.asyncio
async def test_detailed_health_db_failure(monkeypatch, async_client):
    from app.api.system import health as mod
    from app.main import app

    class BadSession:
        async def execute(self, q):
            raise RuntimeError("db fail")

    async def fake_get_db():
        yield BadSession()

    app.dependency_overrides[mod.get_db] = fake_get_db

    r = await async_client.get("/system/health/detailed")
    app.dependency_overrides.clear()
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "degraded"
    assert data["checks"]["database"]["status"] == "unhealthy"


@pytest.mark.asyncio
async def test_detailed_health_redis_enabled_but_no_client(monkeypatch, async_client):
    from app.api.system import health as mod
    from app.core.config import settings
    from app.main import app

    monkeypatch.setattr(settings, "ENABLE_REDIS", True, raising=False)

    # DB ok
    class R:
        def fetchone(self):
            return (1,)

    class GoodSession:
        async def execute(self, q):
            return R()

    async def fake_get_db():
        yield GoodSession()

    app.dependency_overrides[mod.get_db] = fake_get_db

    # Make get_redis_client return None
    import app.services.external.redis as redis_mod

    monkeypatch.setattr(redis_mod, "get_redis_client", lambda: None, raising=False)

    r = await async_client.get("/system/health/detailed")
    app.dependency_overrides.clear()
    assert r.status_code == 200
    data = r.json()
    assert data["checks"]["redis"]["status"] in {"healthy", "unhealthy"}
    # Should include a response_time key regardless
    assert "response_time" in data["checks"]["redis"]


@pytest.mark.asyncio
async def test_readiness_with_redis_enabled_no_client(monkeypatch, async_client):
    from app.api.system import health as mod
    from app.core.config import settings
    from app.main import app

    monkeypatch.setattr(settings, "ENABLE_REDIS", True, raising=False)

    # DB ok
    class R:
        def fetchone(self):
            return (1,)

    class GoodSession:
        async def execute(self, q):
            return R()

    async def fake_get_db():
        yield GoodSession()

    app.dependency_overrides[mod.get_db] = fake_get_db

    # get_redis_client returns None
    import app.services.external.redis as redis_mod

    monkeypatch.setattr(redis_mod, "get_redis_client", lambda: None, raising=False)

    r = await async_client.get("/system/health/ready")
    app.dependency_overrides.clear()
    assert r.status_code == 200
    assert r.json()["ready"] is True


@pytest.mark.asyncio
async def test_test_sentry_endpoint_returns_500(async_client):
    r = await async_client.get("/system/health/test-sentry")
    assert r.status_code == 500
