import logging
import logging.handlers
import os
import sys
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any

import structlog
from structlog.stdlib import LoggerFactory

from app.core.config import settings


def setup_logging() -> None:
    """Configure logging with structlog for structured logging."""

    # Create logs directory if file logging is enabled
    if settings.ENABLE_FILE_LOGGING:
        log_dir = Path(settings.LOG_FILE_PATH).parent
        log_dir.mkdir(parents=True, exist_ok=True)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            _add_extra_fields,
            _format_log,
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Add console handler
    console_handler = _create_console_handler()
    root_logger.addHandler(console_handler)

    # Add file handler if enabled
    if settings.ENABLE_FILE_LOGGING:
        file_handler = _create_file_handler()
        root_logger.addHandler(file_handler)

    # Set specific loggers to appropriate levels
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("redis").setLevel(logging.WARNING)


def _add_extra_fields(
    logger: Any, method_name: str, event_dict: MutableMapping[str, object]
) -> MutableMapping[str, object]:
    """Add extra fields to log entries."""
    if settings.LOG_INCLUDE_PID:
        event_dict["pid"] = os.getpid()

    if settings.LOG_INCLUDE_THREAD:
        import threading

        event_dict["thread"] = threading.current_thread().name

    # Add environment info
    event_dict["environment"] = settings.ENVIRONMENT
    event_dict["service"] = settings.PROJECT_NAME.lower().replace(" ", "_")

    return event_dict


def _format_log(
    logger: Any, method_name: str, event_dict: MutableMapping[str, object]
) -> str:
    """Format log entry based on configuration."""
    if settings.LOG_FORMAT.lower() == "json":
        rendered = structlog.processors.JSONRenderer()(logger, method_name, event_dict)
        return str(rendered)
    else:
        rendered = structlog.dev.ConsoleRenderer(colors=settings.ENABLE_COLORED_LOGS)(
            logger, method_name, event_dict
        )
        return str(rendered)


def _create_console_handler() -> logging.StreamHandler:
    """Create console handler with appropriate formatting."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    if settings.LOG_FORMAT.lower() == "json":
        # For JSON format, we use the structlog processor
        handler.setFormatter(logging.Formatter("%(message)s"))
    else:
        # For text format, create a custom formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

    return handler


def _create_file_handler() -> logging.handlers.RotatingFileHandler:
    """Create rotating file handler for log files."""
    # Parse max size (e.g., "10MB" -> 10 * 1024 * 1024)
    max_size_str = settings.LOG_FILE_MAX_SIZE.upper()
    if max_size_str.endswith("MB"):
        max_bytes = int(max_size_str[:-2]) * 1024 * 1024
    elif max_size_str.endswith("KB"):
        max_bytes = int(max_size_str[:-2]) * 1024
    elif max_size_str.endswith("GB"):
        max_bytes = int(max_size_str[:-2]) * 1024 * 1024 * 1024
    else:
        max_bytes = int(max_size_str)

    handler = logging.handlers.RotatingFileHandler(
        filename=settings.LOG_FILE_PATH,
        maxBytes=max_bytes,
        backupCount=settings.LOG_FILE_BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    if settings.LOG_FORMAT.lower() == "json":
        handler.setFormatter(logging.Formatter("%(message)s"))
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

    return handler


def get_logger(name: str) -> Any:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


# Convenience function for common loggers
def get_app_logger() -> Any:
    """Get the main application logger."""
    return get_logger("app")


def get_api_logger() -> Any:
    """Get the API logger."""
    return get_logger("api")


def get_db_logger() -> Any:
    """Get the database logger."""
    return get_logger("database")


def get_auth_logger() -> Any:
    """Get the authentication logger."""
    return get_logger("auth")
