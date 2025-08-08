import logging
import os
import tempfile

import pytest


@pytest.mark.unit
def test_setup_logging_with_file_logging_json(monkeypatch):
    from app.core.config import config as cfg
    from app.core.config import logging_config as lc

    tmpdir = tempfile.mkdtemp()
    logfile = os.path.join(tmpdir, "app.log")

    monkeypatch.setattr(cfg.settings, "ENABLE_FILE_LOGGING", True, raising=False)
    monkeypatch.setattr(cfg.settings, "LOG_FILE_PATH", logfile, raising=False)
    monkeypatch.setattr(cfg.settings, "LOG_FILE_MAX_SIZE", "1MB", raising=False)
    monkeypatch.setattr(cfg.settings, "LOG_FILE_BACKUP_COUNT", 1, raising=False)
    monkeypatch.setattr(cfg.settings, "LOG_LEVEL", "INFO", raising=False)
    monkeypatch.setattr(cfg.settings, "LOG_FORMAT", "json", raising=False)

    lc.setup_logging()
    logger = lc.get_app_logger()
    logger.info("hello-json", test=True)

    # Ensure a RotatingFileHandler was added
    root = logging.getLogger()
    assert any(
        isinstance(h, logging.handlers.RotatingFileHandler) for h in root.handlers
    )


@pytest.mark.unit
def test_setup_logging_text_and_helpers(monkeypatch):
    from app.core.config import config as cfg
    from app.core.config import logging_config as lc

    monkeypatch.setattr(cfg.settings, "ENABLE_FILE_LOGGING", False, raising=False)
    monkeypatch.setattr(cfg.settings, "LOG_LEVEL", "DEBUG", raising=False)
    monkeypatch.setattr(cfg.settings, "LOG_FORMAT", "text", raising=False)
    monkeypatch.setattr(cfg.settings, "ENABLE_COLORED_LOGS", False, raising=False)

    lc.setup_logging()
    # Exercise helper getters
    assert lc.get_app_logger() is not None
    assert lc.get_api_logger() is not None
    assert lc.get_db_logger() is not None
    assert lc.get_auth_logger() is not None
