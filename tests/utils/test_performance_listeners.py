import importlib
import time
from importlib import reload


def test_sqlalchemy_listeners_capture_and_invoke(monkeypatch):
    captured = {"before": None, "after": None, "debug": 0, "warn": 0}

    # Fake listens_for to capture registered functions
    def fake_listens_for(target, name):  # type: ignore[no-untyped-def]
        def decorator(fn):  # type: ignore[no-untyped-def]
            if name == "before_cursor_execute":
                captured["before"] = fn
            if name == "after_cursor_execute":
                captured["after"] = fn
            return fn

        return decorator

    import sqlalchemy.event as event

    monkeypatch.setattr(event, "listens_for", fake_listens_for)

    # Fake logger to count
    def fake_debug(self, *a, **k):  # type: ignore[no-untyped-def]
        captured["debug"] += 1

    def fake_warning(self, *a, **k):  # type: ignore[no-untyped-def]
        captured["warn"] += 1

    # Reload module to register listeners with our fake decorator
    m = reload(importlib.import_module("app.utils.performance"))
    monkeypatch.setattr(
        m, "logger", type("L", (), {"debug": fake_debug, "warning": fake_warning})()
    )

    # Call captured listeners
    class Conn:
        def __init__(self):
            self.info = {}

    conn = Conn()

    # Invoke before to push start time
    captured_before = captured["before"]
    captured_after = captured["after"]
    assert captured_before and captured_after

    captured_before(conn, None, "SELECT 1", {}, None, False)  # type: ignore[misc]
    assert "query_start_time" in conn.info

    # Prepare a slow start time to trigger warning
    conn.info["query_start_time"][-1] = time.time() - 0.2
    captured_after(conn, None, "SELECT 1", {}, None, False)  # type: ignore[misc]

    assert captured["debug"] >= 1
    slow_warns = captured["warn"]
    assert slow_warns >= 1

    # Now cover the fast-path (no warning): push new start time and call after without delay
    captured_before(conn, None, "SELECT 2", {}, None, False)  # type: ignore[misc]
    # Do not adjust start time; elapsed ~0 -> no warning branch
    captured_after(conn, None, "SELECT 2", {}, None, False)  # type: ignore[misc]

    # Ensure warning count did not increase on fast path
    assert captured["warn"] == slow_warns
