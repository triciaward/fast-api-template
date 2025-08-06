#!/usr/bin/env python3
"""
Logging Demo Script

This script demonstrates the logging configuration and features
of the FastAPI template.
"""

import sys
from pathlib import Path

from app.core.config import settings
from app.core.logging_config import (
    get_app_logger,
    get_auth_logger,
    get_db_logger,
    setup_logging,
)

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))


def demo_basic_logging() -> None:
    """Demonstrate basic logging functionality."""
    logger = get_app_logger()
    logger.info("Application started", version=settings.VERSION)
    logger.warning("This is a warning message", component="demo")
    logger.error("This is an error message", error_code="DEMO_001")
    logger.info(
        "User action performed",
        user_id="12345",
        action="login",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0...",
    )


def demo_auth_logging() -> None:
    """Demonstrate authentication-specific logging."""
    auth_logger = get_auth_logger()
    auth_logger.info("Login attempt", email="user@example.com", ip="192.168.1.100")
    auth_logger.warning(
        "Failed login attempt",
        email="user@example.com",
        reason="invalid_password",
    )
    auth_logger.info(
        "Successful login",
        user_id="12345",
        email="user@example.com",
        login_method="password",
    )
    auth_logger.info("OAuth login attempt", provider="google", email="user@gmail.com")
    auth_logger.info(
        "OAuth login successful",
        user_id="12345",
        provider="google",
        email="user@gmail.com",
    )


def demo_database_logging() -> None:
    """Demonstrate database-specific logging."""
    db_logger = get_db_logger()
    db_logger.info(
        "Database connection established",
        connection_id="conn_001",
        database="fastapi_template",
    )
    db_logger.info(
        "Query executed",
        query_type="SELECT",
        table="users",
        execution_time_ms=15.5,
    )
    db_logger.warning(
        "Slow query detected",
        query_type="SELECT",
        table="users",
        execution_time_ms=2500.0,
        threshold_ms=1000.0,
    )
    db_logger.error(
        "Database connection failed",
        error="connection_timeout",
        retry_count=3,
    )


def demo_error_logging() -> None:
    """Demonstrate error logging with exceptions."""
    logger = get_app_logger()
    try:
        _ = 10 / 0
    except ZeroDivisionError:
        logger.error(
            "Division by zero error occurred",
            operation="division",
            dividend=10,
            divisor=0,
            exc_info=True,
        )
    try:
        raise ValueError("Invalid input provided")
    except ValueError as e:
        logger.error(
            "Validation error",
            error_type="value_error",
            message=str(e),
            exc_info=True,
        )


def demo_different_formats() -> None:
    """Demonstrate different log formats."""
    with open(".env", "a") as f:
        f.write("\nLOG_FORMAT=json\n")
    setup_logging()
    logger = get_app_logger()
    logger.info("JSON format test", test_field="json_value")
    with open(".env", "a") as f:
        f.write("\nLOG_FORMAT=text\n")
    setup_logging()
    logger = get_app_logger()
    logger.info("Text format test", test_field="text_value")


def main() -> None:
    """Main demo function."""
    setup_logging()
    demo_basic_logging()
    demo_auth_logging()
    demo_database_logging()
    demo_error_logging()


if __name__ == "__main__":
    main()
