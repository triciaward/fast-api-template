import pytest


class FakeRedis:
    async def ping(self):
        return True


@pytest.mark.asyncio
async def test_detailed_health_with_redis_enabled(monkeypatch, async_client):
    from app.core.config import settings
    from app.services.external import redis as redis_mod

    # Enable Redis
    monkeypatch.setattr(settings, "ENABLE_REDIS", True)

    # Inject a fake global Redis client
    monkeypatch.setattr(redis_mod, "redis_client", FakeRedis())

    resp = await async_client.get(
        "/system/health/detailed", headers={"user-agent": "pytest"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["checks"]["redis"]["status"] == "healthy"


@pytest.mark.asyncio
async def test_detailed_health_redis_unhealthy(monkeypatch, async_client):
    from app.core.config import settings
    from app.services.external import redis as redis_mod

    monkeypatch.setattr(settings, "ENABLE_REDIS", True)

    class BadRedis:
        async def ping(self):
            raise RuntimeError("down")

    monkeypatch.setattr(redis_mod, "redis_client", BadRedis())

    resp = await async_client.get(
        "/system/health/detailed", headers={"user-agent": "pytest"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["checks"]["redis"]["status"] == "unhealthy"


@pytest.mark.asyncio
async def test_readiness_with_redis_enabled(monkeypatch, async_client):
    from app.api.system import health as health_mod
    from app.core.config import settings
    from app.main import app
    from app.services.external import redis as redis_mod

    monkeypatch.setattr(settings, "ENABLE_REDIS", True)
    monkeypatch.setattr(redis_mod, "redis_client", FakeRedis())

    class FakeSession:
        async def execute(self, *args, **kwargs):
            class R:
                def fetchone(self):
                    return (1,)

            return R()

    async def fake_get_db():
        yield FakeSession()

    # Override FastAPI dependency to avoid real DB access
    app.dependency_overrides[health_mod.get_db] = fake_get_db

    resp = await async_client.get(
        "/system/health/ready", headers={"user-agent": "pytest"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ready"] is True
