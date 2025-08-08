import importlib
import sys

import pytest


@pytest.mark.unit
def test_main_hsts_and_sentry_middleware(monkeypatch):
    from app.core.config import config as cfg

    # Turn on sentry and HSTS
    monkeypatch.setattr(cfg.settings, "ENABLE_SENTRY", True, raising=False)
    monkeypatch.setattr(cfg.settings, "ENABLE_HSTS", True, raising=False)

    # Ensure rate limiting flag does not block other branches
    monkeypatch.setattr(cfg.settings, "ENABLE_RATE_LIMITING", False, raising=False)

    # Reload app.main to run module-level middleware configuration
    if "app.main" in sys.modules:
        del sys.modules["app.main"]
    mod = importlib.import_module("app.main")

    assert hasattr(mod, "app")
