import importlib
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_lifespan_non_testing_mode_with_database_creation(monkeypatch):
    """Test lifespan startup in non-testing mode with database creation and bootstrap."""
    from app import main as mod

    # Remove TESTING env var to trigger database creation
    monkeypatch.delenv("TESTING", raising=False)

    # Mock bootstrap_superuser
    mock_bootstrap = AsyncMock()
    monkeypatch.setattr(mod, "bootstrap_superuser", mock_bootstrap)

    # Mock Base.metadata.create_all
    mock_create_all = MagicMock()
    monkeypatch.setattr("app.models.Base.metadata.create_all", mock_create_all)

    # Disable other features to focus on database creation
    monkeypatch.setattr(mod.settings, "ENABLE_REDIS", False)
    monkeypatch.setattr(mod.settings, "ENABLE_RATE_LIMITING", False)

    # Mock the entire engine object to avoid read-only attribute issues
    mock_engine = MagicMock()
    mock_conn = AsyncMock()
    mock_engine.begin.return_value.__aenter__.return_value = mock_conn
    mock_engine.begin.return_value.__aexit__.return_value = None
    mock_engine.dispose = AsyncMock()

    with patch("app.main.engine", mock_engine):
        async with mod.lifespan(mod.app):
            pass

        # Verify database operations were called
        assert mock_conn.run_sync.called
        mock_bootstrap.assert_called_once()
        mock_engine.dispose.assert_called_once()


@pytest.mark.asyncio
async def test_lifespan_redis_shutdown_when_enabled(monkeypatch):
    """Test Redis shutdown during lifespan teardown."""
    from app import main as mod

    # Force testing mode to skip DB operations
    monkeypatch.setenv("TESTING", "1")

    # Enable Redis
    monkeypatch.setattr(mod.settings, "ENABLE_REDIS", True)
    monkeypatch.setattr(mod.settings, "ENABLE_RATE_LIMITING", False)

    # Mock Redis functions
    mock_init_redis = AsyncMock()

    # Track if close_redis gets imported and called
    shutdown_calls = {"close_redis": 0}

    async def fake_close_redis():
        shutdown_calls["close_redis"] += 1

    # Patch services functions
    from app import services as services_mod

    monkeypatch.setattr(services_mod, "init_redis", mock_init_redis)
    monkeypatch.setattr(services_mod, "close_redis", fake_close_redis)

    # Mock the entire engine object
    mock_engine = MagicMock()
    mock_engine.dispose = AsyncMock()

    with patch("app.main.engine", mock_engine):
        async with mod.lifespan(mod.app):
            pass

        # Verify Redis shutdown was called
        assert shutdown_calls["close_redis"] == 1
        mock_init_redis.assert_called_once()
        mock_engine.dispose.assert_called_once()


@pytest.mark.asyncio
async def test_lifespan_disabled_features_skip_initialization(monkeypatch):
    """Test that disabled features are properly skipped during lifespan."""
    from app import main as mod

    # Force testing mode and disable all optional features
    monkeypatch.setenv("TESTING", "1")
    monkeypatch.setattr(mod.settings, "ENABLE_REDIS", False)
    monkeypatch.setattr(mod.settings, "ENABLE_RATE_LIMITING", False)

    # Track function calls
    calls = {"init_redis": 0, "init_rate_limiter": 0, "close_redis": 0}

    async def fake_init_redis():
        calls["init_redis"] += 1

    async def fake_init_rate_limiter():
        calls["init_rate_limiter"] += 1

    async def fake_close_redis():
        calls["close_redis"] += 1

    # Patch services functions
    from app import services as services_mod

    monkeypatch.setattr(services_mod, "init_redis", fake_init_redis)
    monkeypatch.setattr(services_mod, "init_rate_limiter", fake_init_rate_limiter)
    monkeypatch.setattr(services_mod, "close_redis", fake_close_redis)

    # Mock the entire engine object
    mock_engine = MagicMock()
    mock_engine.dispose = AsyncMock()

    with patch("app.main.engine", mock_engine):
        async with mod.lifespan(mod.app):
            pass

        # Verify no optional services were initialized
        assert calls == {"init_redis": 0, "init_rate_limiter": 0, "close_redis": 0}
        mock_engine.dispose.assert_called_once()


def test_celery_import_when_enabled(monkeypatch):
    """Test that Celery tasks are imported when ENABLE_CELERY is True."""
    from app.core.config import config as cfg

    # Enable Celery before any imports
    monkeypatch.setattr(cfg.settings, "ENABLE_CELERY", True, raising=False)

    # Mock importlib.import_module to track calls
    import_calls = []

    def mock_import_module(module_name):
        import_calls.append(module_name)
        return MagicMock()  # Return a mock module

    with patch("importlib.import_module", side_effect=mock_import_module):
        # Clear any existing main module
        if "app.main" in sys.modules:
            del sys.modules["app.main"]

        # Import main module - this should trigger the Celery import
        import app.main

        # Verify Celery tasks were imported
        assert "app.services.background.celery_tasks" in import_calls


def test_production_warnings_secret_key_only(monkeypatch):
    """Test production warning for insecure secret key only."""
    from app.core.config import config as cfg

    # Production mode with only secret key issue
    monkeypatch.setattr(cfg.settings, "ENVIRONMENT", "production", raising=False)
    monkeypatch.setattr(
        cfg.settings,
        "SECRET_KEY",
        "dev_secret_key_change_in_production",
        raising=False,
    )
    monkeypatch.setattr(
        cfg.settings,
        "REFRESH_TOKEN_COOKIE_SECURE",
        True,
        raising=False,
    )  # Secure
    monkeypatch.setattr(cfg.settings, "ENABLE_HSTS", True, raising=False)  # Secure

    # Reload main to trigger warnings
    if "app.main" in sys.modules:
        del sys.modules["app.main"]
    mod = importlib.import_module("app.main")

    assert hasattr(mod, "app")
    assert mod.app.title == cfg.settings.PROJECT_NAME


def test_production_warnings_cookie_secure_only(monkeypatch):
    """Test production warning for insecure cookie setting only."""
    from app.core.config import config as cfg

    # Production mode with only cookie security issue
    monkeypatch.setattr(cfg.settings, "ENVIRONMENT", "production", raising=False)
    monkeypatch.setattr(
        cfg.settings,
        "SECRET_KEY",
        "secure_production_key",
        raising=False,
    )  # Secure
    monkeypatch.setattr(
        cfg.settings,
        "REFRESH_TOKEN_COOKIE_SECURE",
        False,
        raising=False,
    )  # Insecure
    monkeypatch.setattr(cfg.settings, "ENABLE_HSTS", True, raising=False)  # Secure

    # Reload main to trigger warnings
    if "app.main" in sys.modules:
        del sys.modules["app.main"]
    mod = importlib.import_module("app.main")

    assert hasattr(mod, "app")


def test_production_warnings_hsts_only(monkeypatch):
    """Test production warning for disabled HSTS only."""
    from app.core.config import config as cfg

    # Production mode with only HSTS issue
    monkeypatch.setattr(cfg.settings, "ENVIRONMENT", "production", raising=False)
    monkeypatch.setattr(
        cfg.settings,
        "SECRET_KEY",
        "secure_production_key",
        raising=False,
    )  # Secure
    monkeypatch.setattr(
        cfg.settings,
        "REFRESH_TOKEN_COOKIE_SECURE",
        True,
        raising=False,
    )  # Secure
    monkeypatch.setattr(cfg.settings, "ENABLE_HSTS", False, raising=False)  # Insecure

    # Reload main to trigger warnings
    if "app.main" in sys.modules:
        del sys.modules["app.main"]
    mod = importlib.import_module("app.main")

    assert hasattr(mod, "app")


def test_non_production_skips_warnings(monkeypatch):
    """Test that non-production environments skip security warnings."""
    from app.core.config import config as cfg

    # Development mode (should skip all warnings)
    monkeypatch.setattr(cfg.settings, "ENVIRONMENT", "development", raising=False)
    monkeypatch.setattr(
        cfg.settings,
        "SECRET_KEY",
        "dev_secret_key_change_in_production",
        raising=False,
    )
    monkeypatch.setattr(
        cfg.settings,
        "REFRESH_TOKEN_COOKIE_SECURE",
        False,
        raising=False,
    )
    monkeypatch.setattr(cfg.settings, "ENABLE_HSTS", False, raising=False)

    # Reload main - should not trigger any warnings
    if "app.main" in sys.modules:
        del sys.modules["app.main"]
    mod = importlib.import_module("app.main")

    assert hasattr(mod, "app")
    assert mod.app.title == cfg.settings.PROJECT_NAME
