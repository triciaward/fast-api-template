import logging

import pytest


@pytest.mark.unit
def test_setup_logging_text_format(monkeypatch):
    from app.core.config import config as cfg
    from app.core.config import logging_config as lc

    monkeypatch.setattr(cfg.settings, "ENABLE_FILE_LOGGING", False, raising=False)
    monkeypatch.setattr(cfg.settings, "LOG_FORMAT", "text", raising=False)
    monkeypatch.setattr(cfg.settings, "LOG_LEVEL", "INFO", raising=False)
    monkeypatch.setattr(cfg.settings, "ENABLE_COLORED_LOGS", False, raising=False)

    lc.setup_logging()
    logger = lc.get_app_logger()
    logger.info("hello", test=True)
    # No exception indicates formatter configured


@pytest.mark.unit
def test_setup_logging_json_format_and_file_handler(monkeypatch, tmp_path):
    from app.core.config import config as cfg
    from app.core.config import logging_config as lc

    monkeypatch.setattr(cfg.settings, "ENABLE_FILE_LOGGING", True, raising=False)
    log_file = tmp_path / "app.log"
    monkeypatch.setattr(cfg.settings, "LOG_FILE_PATH", str(log_file), raising=False)
    monkeypatch.setattr(cfg.settings, "LOG_FILE_MAX_SIZE", "1MB", raising=False)
    monkeypatch.setattr(cfg.settings, "LOG_FILE_BACKUP_COUNT", 1, raising=False)
    monkeypatch.setattr(cfg.settings, "LOG_FORMAT", "json", raising=False)
    monkeypatch.setattr(cfg.settings, "LOG_LEVEL", "WARNING", raising=False)

    lc.setup_logging()
    logger = lc.get_logger("test")
    logger.warning("warn", value=1)
    # Ensure the file handler can be created and used
    root_handlers = logging.getLogger().handlers
    assert any(isinstance(h, logging.handlers.RotatingFileHandler) for h in root_handlers)


@pytest.mark.unit
def test_helper_getters_return_loggers():
    from app.core.config import logging_config as lc

    assert lc.get_api_logger() is not None
    assert lc.get_db_logger() is not None
    assert lc.get_auth_logger() is not None
