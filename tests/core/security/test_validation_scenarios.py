import pytest

pytestmark = pytest.mark.unit


def test_validate_email_disposable_domain():
    from app.core.security.validation import validate_email_format

    ok, msg = validate_email_format("user@mailinator.com")
    assert ok is False
    assert "disposable" in msg.lower()


def test_validate_username_reserved_and_consecutive():
    from app.core.security.validation import validate_username

    ok, msg = validate_username("admin")
    assert ok is False
    assert "reserved" in msg.lower()

    ok, msg = validate_username("user__name")
    assert ok is False
    assert "consecutive" in msg.lower()


def test_clean_and_sanitize_input():
    from app.core.security.validation import clean_input, sanitize_input

    assert clean_input("  a\x00b  ") == "ab"
    assert sanitize_input("  a\x00b  ", max_length=2) == "ab"


