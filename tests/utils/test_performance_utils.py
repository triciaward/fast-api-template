import asyncio
import types


def test_add_performance_headers():
    from app.utils.performance import add_performance_headers

    resp = types.SimpleNamespace(headers={})
    add_performance_headers(resp, 0.123)
    assert resp.headers["X-Execution-Time"] == "0.123"
    assert resp.headers["X-Cache-Status"] == "MISS"


def test_optimize_query_applies_limit():
    from app.utils.performance import optimize_query

    class Q:
        def __init__(self):
            self._limit = None

        def limit(self, n):  # type: ignore[no-untyped-def]
            self._limit = n
            return self

    q = Q()
    q2 = optimize_query(q, limit=5)
    assert q2._limit == 5


def test_cache_result_decorator(monkeypatch):
    from app.utils import performance as perf

    # Ensure a clean cache
    perf._performance_cache.clear()

    calls = {"count": 0}

    @perf.cache_result(ttl=60)
    async def expensive(x):  # type: ignore[no-untyped-def]
        calls["count"] += 1
        await asyncio.sleep(0)
        return x * 2

    # First call — miss
    out1 = asyncio.run(expensive(2))
    # Second call — hit
    out2 = asyncio.run(expensive(2))
    assert out1 == out2 == 4
    assert calls["count"] == 1


def test_monitor_request_performance_logs(monkeypatch):
    from app.utils import performance as perf

    logs = {"level": None}

    def fake_warning(*args, **kwargs):  # type: ignore[no-untyped-def]
        logs["level"] = "warning"

    def fake_debug(*args, **kwargs):  # type: ignore[no-untyped-def]
        logs["level"] = "debug"

    monkeypatch.setattr(
        perf,
        "logger",
        types.SimpleNamespace(
            warning=fake_warning, debug=fake_debug, exception=lambda *a, **k: None
        ),
    )

    @perf.monitor_request_performance()
    async def fast():  # type: ignore[no-untyped-def]
        await asyncio.sleep(0)
        return "ok"

    out = asyncio.run(fast())
    assert out == "ok"
    assert logs["level"] in {"debug", "warning"}
