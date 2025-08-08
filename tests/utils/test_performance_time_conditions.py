import asyncio


def test_monitor_request_performance_time_branches(monkeypatch):
    from app.utils import performance as perf

    # Fake time to control durations precisely
    class FakeTime:
        def __init__(self):
            self.t = 1000.0

        def time(self):  # type: ignore[no-untyped-def]
            return self.t

        def advance(self, dt):  # type: ignore[no-untyped-def]
            self.t += dt

    ft = FakeTime()
    monkeypatch.setattr(perf, "time", ft)

    logs = {"warn": 0, "debug": 0}

    def fake_warning(self, *a, **k):  # type: ignore[no-untyped-def]
        logs["warn"] += 1

    def fake_debug(self, *a, **k):  # type: ignore[no-untyped-def]
        logs["debug"] += 1

    monkeypatch.setattr(perf, "logger", type("L", (), {"warning": fake_warning, "debug": fake_debug, "exception": lambda *a, **k: None})())

    @perf.monitor_request_performance()
    async def ffast():  # type: ignore[no-untyped-def]
        ft.advance(0.5)  # under threshold
        return "ok"

    @perf.monitor_request_performance()
    async def fslow():  # type: ignore[no-untyped-def]
        ft.advance(1.5)  # over threshold
        return "ok"

    assert asyncio.run(ffast()) == "ok"
    assert asyncio.run(fslow()) == "ok"
    assert logs["debug"] >= 1 and logs["warn"] >= 1


def test_cache_result_remaining_paths(monkeypatch):
    import asyncio

    from app.utils import performance as perf

    perf._performance_cache.clear()

    # Ensure hash key path and update
    calls = {"n": 0}

    @perf.cache_result(ttl=0)
    async def fn(x, y=1):  # type: ignore[no-untyped-def]
        calls["n"] += 1
        return x + y

    # ttl=0 ensures miss twice
    assert asyncio.run(fn(1)) == 2
    assert asyncio.run(fn(1)) == 2
    assert calls["n"] == 2

