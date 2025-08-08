import asyncio


def test_monitor_request_performance_all_logging_paths(monkeypatch):
    from app.utils import performance as perf

    times = [1000.0, 1000.5, 1001.0, 1002.6]  # fast: 0.5s, slow: 1.6s

    def fake_time():  # type: ignore[no-untyped-def]
        return times.pop(0)

    logs = {"debug": 0, "warning": 0, "exception": 0}

    def d(self, *a, **k):  # type: ignore[no-untyped-def]
        logs["debug"] += 1

    def w(self, *a, **k):  # type: ignore[no-untyped-def]
        logs["warning"] += 1

    def e(self, *a, **k):  # type: ignore[no-untyped-def]
        logs["exception"] += 1

    monkeypatch.setattr(
        perf,
        "time",
        type("T", (), {"time": staticmethod(fake_time)})(),
    )
    monkeypatch.setattr(
        perf,
        "logger",
        type("L", (), {"debug": d, "warning": w, "exception": e})(),
    )

    @perf.monitor_request_performance()
    async def f1():  # type: ignore[no-untyped-def]
        return "ok"

    @perf.monitor_request_performance()
    async def f2():  # type: ignore[no-untyped-def]
        return "ok"

    assert asyncio.run(f1()) == "ok"
    assert asyncio.run(f2()) == "ok"
    assert logs["debug"] >= 1 and logs["warning"] >= 1


def test_monitor_request_performance_exception_logs(monkeypatch):
    from app.utils import performance as perf

    times = [1000.0, 1001.5]

    def fake_time():  # type: ignore[no-untyped-def]
        return times.pop(0)

    logs = {"exception": 0}

    def e(self, *a, **k):  # type: ignore[no-untyped-def]
        logs["exception"] += 1

    monkeypatch.setattr(
        perf,
        "time",
        type("T", (), {"time": staticmethod(fake_time)})(),
    )
    monkeypatch.setattr(
        perf,
        "logger",
        type(
            "L",
            (),
            {
                "debug": lambda *a, **k: None,
                "warning": lambda *a, **k: None,
                "exception": e,
            },
        )(),
    )

    @perf.monitor_request_performance()
    async def boom():  # type: ignore[no-untyped-def]
        raise RuntimeError("x")

    import pytest

    with pytest.raises(RuntimeError):
        asyncio.run(boom())
    assert logs["exception"] == 1


def test_add_performance_headers_and_cache_result_edge(monkeypatch):
    from app.utils import performance as perf

    resp = type("R", (), {"headers": {}})()
    perf.add_performance_headers(resp, 0.001)
    assert resp.headers["X-Execution-Time"] == "0.001"
    assert resp.headers["X-Cache-Status"] == "MISS"

    perf._performance_cache.clear()

    @perf.cache_result(ttl=1)
    async def g(a, b=2):  # type: ignore[no-untyped-def]
        return a + b

    # Ensure cache key path with kwargs
    import asyncio as aio

    assert aio.run(g(1, b=3)) == 4
    assert aio.run(g(1, b=3)) == 4
