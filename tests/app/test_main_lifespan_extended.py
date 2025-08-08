import pytest

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_lifespan_initializes_rate_limit_and_redis(monkeypatch):
    from app import main as mod

    # Force TESTING so DB create executes or is skipped appropriately
    monkeypatch.setenv("TESTING", "1")

    # toggle features
    monkeypatch.setattr(mod.settings, "ENABLE_REDIS", True)
    monkeypatch.setattr(mod.settings, "ENABLE_RATE_LIMITING", True)
    monkeypatch.setattr(mod.settings, "ENABLE_SENTRY", False)

    # stub init functions
    init_calls = {"redis": 0, "rl": 0}

    async def fake_init_redis():
        init_calls["redis"] += 1

    async def fake_init_rl():
        init_calls["rl"] += 1

    # Patch services functions imported in lifespan body
    from app import services as services_mod

    monkeypatch.setattr(services_mod, "init_redis", fake_init_redis)
    monkeypatch.setattr(services_mod, "init_rate_limiter", fake_init_rl)

    # Run lifespan context manually
    async with mod.lifespan(mod.app):
        pass

    assert init_calls == {"redis": 1, "rl": 1}


@pytest.mark.asyncio
async def test_middleware_setup_toggles(monkeypatch):
    # Patch settings to enable sentry and rate limiting
    from app import main as mod

    monkeypatch.setattr(mod.settings, "ENABLE_SECURITY_HEADERS", False)
    monkeypatch.setattr(mod.settings, "ENABLE_SENTRY", True)
    monkeypatch.setattr(mod.settings, "ENABLE_RATE_LIMITING", True)

    added = {"sentry": False, "rl": False}

    # Capture add_middleware calls
    import fastapi.applications as fa_apps

    def fake_add_middleware(self, middleware_class, *args, **kwargs):
        added["sentry"] = True
        return

    monkeypatch.setattr(fa_apps.FastAPI, "add_middleware", fake_add_middleware)

    def fake_setup_rl(app):
        added["rl"] = True

    # Patch rate limiter setup in services before reload
    from app import services as services_mod

    monkeypatch.setattr(services_mod, "setup_rate_limiting", fake_setup_rl)

    # Reload main to execute conditional blocks
    import importlib

    importlib.reload(mod)

    assert added["sentry"] is True
    assert added["rl"] is True
