import importlib
import sys

import pytest


@pytest.mark.unit
def test_system_router_excludes_celery_when_disabled(monkeypatch):
    from app.core.config import config as cfg

    monkeypatch.setattr(cfg.settings, "ENABLE_CELERY", False, raising=False)
    if "app.api.system" in sys.modules:
        del sys.modules["app.api.system"]
    sys_mod = importlib.import_module("app.api.system")

    paths = {getattr(r, "path", None) for r in sys_mod.router.routes}
    # Should not include Celery task routes when disabled
    assert not any(
        "/tasks/" in (p or "") or (p or "").endswith("/status") for p in paths
    )


@pytest.mark.unit
def test_system_router_includes_celery_when_enabled(monkeypatch):
    from app.core.config import config as cfg

    monkeypatch.setattr(cfg.settings, "ENABLE_CELERY", True, raising=False)
    if "app.api.system" in sys.modules:
        del sys.modules["app.api.system"]
    sys_mod = importlib.import_module("app.api.system")

    paths = {getattr(r, "path", None) for r in sys_mod.router.routes}
    # Expect Celery task routes like /system/tasks/submit
    # Note: The actual path will be /system/tasks/submit (without /api prefix)
    # because this test is checking the router directly, not the full app
    assert any((p or "") == "/system/tasks/submit" for p in paths)
