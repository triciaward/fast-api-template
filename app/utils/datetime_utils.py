"""
Datetime utilities for the FastAPI application.

Provides common datetime functions used across the application.
"""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """
    Get current UTC datetime (replaces deprecated datetime.utcnow()).

    Returns:
        datetime: Current UTC datetime with timezone info
    """
    return datetime.now(timezone.utc)


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format a datetime object as a string."""
    return dt.strftime(format_str)


def parse_datetime(
    date_string: str, format_str: str = "%Y-%m-%d %H:%M:%S"
) -> datetime | None:
    """Parse a datetime string into a datetime object."""
    try:
        # Check if format includes timezone info
        if "%z" in format_str or "%Z" in format_str:
            # Parse with timezone info
            return datetime.strptime(date_string, format_str)  # noqa: DTZ007
        # Parse as naive datetime and assume UTC
        # We handle timezone properly by adding UTC timezone
        naive_dt = datetime.strptime(date_string, format_str)  # noqa: DTZ007
        return naive_dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def is_expired(dt: datetime) -> bool:
    """Check if a datetime has expired (is in the past)."""
    return dt < utc_now()


def time_until(dt: datetime) -> float | None:
    """Get seconds until a datetime (negative if already passed)."""
    try:
        delta = dt - utc_now()
        return delta.total_seconds()
    except (TypeError, ValueError):
        return None


def is_near_expiry(dt: datetime, threshold_seconds: int = 86400) -> bool:
    """Check if a datetime is near expiry (within threshold)."""
    seconds_until = time_until(dt)
    if seconds_until is None:
        return False
    return 0 <= seconds_until <= threshold_seconds
