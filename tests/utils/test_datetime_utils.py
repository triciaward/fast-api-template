from datetime import datetime, timedelta, timezone

import pytest


def test_format_and_parse_roundtrip():
    from app.utils.datetime_utils import format_datetime, parse_datetime

    dt = datetime(2025, 1, 1, 12, 34, 56, tzinfo=timezone.utc)
    s = format_datetime(dt)
    parsed = parse_datetime(s)
    assert parsed == datetime(2025, 1, 1, 12, 34, 56, tzinfo=timezone.utc)


def test_is_expired_and_time_until(monkeypatch):
    from app.utils import datetime_utils as du

    fixed_now = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(du, "utc_now", lambda: fixed_now)

    future = fixed_now + timedelta(seconds=10)
    past = fixed_now - timedelta(seconds=5)

    assert du.is_expired(past) is True
    assert du.is_expired(future) is False
    assert du.time_until(future) == 10.0
    assert du.time_until(past) == -5.0


def test_is_near_expiry(monkeypatch):
    from app.utils import datetime_utils as du

    fixed_now = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(du, "utc_now", lambda: fixed_now)

    within = fixed_now + timedelta(seconds=100)
    outside = fixed_now + timedelta(seconds=100000)
    passed = fixed_now - timedelta(seconds=10)

    assert du.is_near_expiry(within, threshold_seconds=200) is True
    assert du.is_near_expiry(outside, threshold_seconds=200) is False
    assert du.is_near_expiry(passed, threshold_seconds=200) is False


from app.utils.datetime_utils import utc_now

pytestmark = pytest.mark.template_only


def test_utc_now_returns_timezone_aware_datetime() -> None:
    dt = utc_now()
    assert dt.tzinfo is not None


def test_format_and_parse_datetime_naive_and_tz():
    """Test datetime formatting and parsing with various timezone scenarios."""
    from app.utils import datetime_utils as du

    # format
    now = datetime(2025, 1, 1, 12, 30, 45, tzinfo=timezone.utc)
    s = du.format_datetime(now)
    assert s.startswith("2025-01-01 12:30:45")

    # parse naive assumes UTC
    parsed = du.parse_datetime("2025-01-01 12:30:45")
    assert parsed.tzinfo == timezone.utc and parsed.year == 2025

    # parse with timezone format
    s_tz = "2025-01-01 12:30:45 +0000"
    parsed_tz = du.parse_datetime(s_tz, "%Y-%m-%d %H:%M:%S %z")
    assert parsed_tz.tzinfo is not None

    # invalid parse returns None
    assert du.parse_datetime("not-a-date") is None


def test_expiry_helpers_extended(monkeypatch):
    """Test additional expiry-related helper functions."""
    from app.utils import datetime_utils as du

    fixed_now = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(du, "utc_now", lambda: fixed_now)

    future = fixed_now + timedelta(seconds=10)
    past = fixed_now - timedelta(seconds=10)

    # is_expired
    assert du.is_expired(past) is True
    assert du.is_expired(future) is False

    # time_until
    assert du.time_until(future) == 10
    assert du.time_until(past) == -10

    # is_near_expiry (threshold default=86400)
    assert du.is_near_expiry(future, threshold_seconds=20) is True
    assert du.is_near_expiry(past, threshold_seconds=20) is False

    # type error path
    assert du.time_until("bad") is None  # type: ignore[arg-type]
