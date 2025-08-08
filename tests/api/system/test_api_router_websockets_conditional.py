import importlib
import sys

import pytest


@pytest.mark.unit
def test_api_router_includes_websockets_when_enabled(monkeypatch):
    from app.core.config import config as cfg

    # Enable websockets and reload app.api
    monkeypatch.setattr(cfg.settings, "ENABLE_WEBSOCKETS", True, raising=False)
    if "app.api" in sys.modules:
        del sys.modules["app.api"]
    api_mod = importlib.import_module("app.api")

    paths = {getattr(r, "path", None) for r in api_mod.api_router.routes}
    # The websockets router is mounted under /integrations
    assert "/integrations/ws/status" in paths


@pytest.mark.unit
def test_api_router_excludes_websockets_when_disabled(monkeypatch):
    from app.core.config import config as cfg

    # Disable websockets and reload app.api
    monkeypatch.setattr(cfg.settings, "ENABLE_WEBSOCKETS", False, raising=False)
    if "app.api" in sys.modules:
        del sys.modules["app.api"]
    api_mod = importlib.import_module("app.api")

    paths = {getattr(r, "path", None) for r in api_mod.api_router.routes}
    assert "/integrations/ws/status" not in paths
