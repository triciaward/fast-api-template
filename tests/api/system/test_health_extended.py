import pytest


@pytest.mark.asyncio
async def test_health_check_database_failure(monkeypatch, async_client):
    from app.api.system import health as mod
    from app.main import app

    class BadSession:
        async def execute(self, q):
            raise RuntimeError("db down")

    async def fake_get_db():
        yield BadSession()

    app.dependency_overrides[mod.get_db] = fake_get_db

    r = await async_client.get("/system/health")
    app.dependency_overrides.clear()
    assert r.status_code == 500


@pytest.mark.asyncio
async def test_readiness_check_failure(monkeypatch, async_client):
    from app.api.system import health as mod
    from app.main import app

    class BadSession:
        async def execute(self, q):
            raise RuntimeError("db not ready")

    async def fake_get_db():
        yield BadSession()

    app.dependency_overrides[mod.get_db] = fake_get_db

    r = await async_client.get("/system/health/ready")
    app.dependency_overrides.clear()
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_database_health_success(monkeypatch, async_client):
    from app.api.system import health as mod
    from app.main import app

    class R1:
        def fetchone(self):
            return (1,)

    class R2:
        def __init__(self, n):
            self.n = n

        def fetchone(self):
            return (self.n,)

    calls = {"n": 0}

    class GoodSession:
        async def execute(self, q):
            calls["n"] += 1
            return R1() if calls["n"] == 1 else R2(7)

    async def fake_get_db():
        yield GoodSession()

    app.dependency_overrides[mod.get_db] = fake_get_db

    r = await async_client.get("/system/health/database")
    app.dependency_overrides.clear()
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy" and data["table_count"] == 7
