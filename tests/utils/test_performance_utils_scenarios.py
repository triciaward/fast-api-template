import asyncio

import pytest

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_cache_result_hits(monkeypatch):
    from app.utils.performance import _performance_cache, cache_result

    _performance_cache.clear()

    calls = {"n": 0}

    @cache_result(ttl=60)
    async def compute(x):
        calls["n"] += 1
        await asyncio.sleep(0)
        return x * 2

    out1 = await compute(2)
    out2 = await compute(2)
    assert out1 == 4 and out2 == 4
    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_monitor_request_performance_slow_and_exception(monkeypatch):
    from app.utils.performance import monitor_request_performance

    events = {"warn": 0, "exc": 0}

    # Patch logger methods indirectly via module logger if needed
    import app.utils.performance as perf

    def fake_warning(*a, **k):
        events["warn"] += 1

    def fake_exception(*a, **k):
        events["exc"] += 1

    monkeypatch.setattr(perf.logger, "warning", lambda *a, **k: fake_warning())
    monkeypatch.setattr(perf.logger, "exception", lambda *a, **k: fake_exception())

    @monitor_request_performance()
    async def slow_ok():
        await asyncio.sleep(1.05)
        return True

    @monitor_request_performance()
    async def boom():
        await asyncio.sleep(0)
        raise RuntimeError("x")

    ok = await slow_ok()
    assert ok is True
    assert events["warn"] >= 1

    with pytest.raises(RuntimeError):
        await boom()
    assert events["exc"] >= 1


def test_add_performance_headers_sets_values():
    from app.utils.performance import add_performance_headers

    class Resp:
        def __init__(self):
            self.headers = {}

    r = Resp()
    add_performance_headers(r, 0.123)
    assert r.headers["X-Execution-Time"] == "0.123"
    assert r.headers["X-Cache-Status"] == "MISS"
