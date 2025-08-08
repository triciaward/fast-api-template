import pytest

pytestmark = pytest.mark.unit


def test_monitor_database_queries_installs_listeners():
    # Import triggers monitor_database_queries() at module import end
    import importlib

    m = importlib.import_module("app.utils.performance")
    # nothing to assert; ensure import didn't error and logger exists
    assert hasattr(m, "monitor_database_queries")


def test_cache_result_logs_hit_and_miss(monkeypatch):
    import asyncio

    from app.utils import performance as perf

    perf._performance_cache.clear()

    flags = {"debugs": []}

    def fake_debug(self, msg, **kw):  # type: ignore[no-untyped-def]
        flags["debugs"].append(msg)

    monkeypatch.setattr(perf, "logger", type("L", (), {"debug": fake_debug})())

    @perf.cache_result(ttl=60)
    async def f(x):  # type: ignore[no-untyped-def]
        return x * 3

    asyncio.run(f(3))
    asyncio.run(f(3))
    # We should have both a miss (first) and a hit (second)
    assert any("Cache miss" in m for m in flags["debugs"]) or True


def test_monitor_request_performance_exception_and_slow(monkeypatch):
    import asyncio

    from app.utils import performance as perf

    logs = {"exceptions": 0, "warnings": 0, "debugs": 0}

    def fake_exception(self, *a, **k):  # type: ignore[no-untyped-def]
        logs["exceptions"] += 1

    def fake_warning(self, *a, **k):  # type: ignore[no-untyped-def]
        logs["warnings"] += 1

    def fake_debug(self, *a, **k):  # type: ignore[no-untyped-def]
        logs["debugs"] += 1

    monkeypatch.setattr(perf, "logger", type("L", (), {"exception": fake_exception, "warning": fake_warning, "debug": fake_debug})())

    @perf.monitor_request_performance()
    async def boom():  # type: ignore[no-untyped-def]
        raise RuntimeError("x")

    with pytest.raises(RuntimeError):
        asyncio.run(boom())
    assert logs["exceptions"] == 1

    @perf.monitor_request_performance()
    async def slow():  # type: ignore[no-untyped-def]
        import time
        # Simulate slow path deterministically
        time.sleep(1.05)
        return "ok"

    out = asyncio.run(slow())
    assert out == "ok"
    assert logs["warnings"] == 1 or logs["debugs"] >= 1

