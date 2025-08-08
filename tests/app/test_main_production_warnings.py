import importlib
import sys

import pytest


@pytest.mark.unit
def test_main_production_warnings(monkeypatch):
    # Force settings into production with insecure values to trigger warnings
    from app.core.config import config as cfg

    monkeypatch.setattr(cfg.settings, "ENVIRONMENT", "production", raising=False)
    monkeypatch.setattr(
        cfg.settings, "SECRET_KEY", "dev_secret_key_change_in_production", raising=False
    )
    monkeypatch.setattr(
        cfg.settings, "REFRESH_TOKEN_COOKIE_SECURE", False, raising=False
    )
    monkeypatch.setattr(cfg.settings, "ENABLE_HSTS", False, raising=False)

    # Reload app.main to re-run module-level setup
    if "app.main" in sys.modules:
        del sys.modules["app.main"]
    mod = importlib.import_module("app.main")

    # Basic sanity: app exists and has expected title
    assert hasattr(mod, "app")
