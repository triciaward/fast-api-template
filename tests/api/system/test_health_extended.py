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
@pytest.mark.skip(reason="Requires full app/database wiring; skip in template")
async def test_health_check_database_failure(monkeypatch, async_client):
    from app.api.system import health as mod
    from app.main import app

    class BadSession:
        async def execute(self, q):
            raise RuntimeError("db down")

    async def fake_get_db():
        yield BadSession()

    app.dependency_overrides[mod.get_db] = fake_get_db

    r = await async_client.get("/api/system/health")
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

    r = await async_client.get("/api/system/health/ready")
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

    r = await async_client.get("/api/system/health/database")
    app.dependency_overrides.clear()
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy" and data["table_count"] == 7
