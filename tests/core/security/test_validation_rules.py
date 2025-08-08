import pytest

pytestmark = pytest.mark.unit


def test_validate_password_all_branches():
    from app.core.security.validation import validate_password

    assert validate_password("Short1!")[0] is False
    assert validate_password("a" * 129 + "A1!")[0] is False
    assert validate_password("nocaps1!")[0] is False
    assert validate_password("NOLOWER1!")[0] is False
    assert validate_password("NoNumber!")[0] is False
    assert validate_password("NoSpecial1")[0] is False
    assert validate_password("password")[0] is False
    assert validate_password("Password1!")[0] is True


def test_validate_username_all_edges():
    from app.core.security.validation import validate_username

    assert validate_username("ab")[0] is False
    assert validate_username("a" * 31)[0] is False
    assert validate_username("bad space")[0] is False
    assert validate_username("_start")[0] is False
    assert validate_username("end-")[0] is False
    assert validate_username("a__b")[0] is False
    assert validate_username("Admin")[0] is False
    assert validate_username("ok_name")[0] is True


def test_clean_and_sanitize_max_length():
    from app.core.security.validation import sanitize_input

    s = sanitize_input("x" * 200, max_length=10)
    assert s == "x" * 10


def test_clean_and_sanitize_empty_inputs():
    from app.core.security.validation import clean_input, sanitize_input

    assert clean_input("") == ""
    assert sanitize_input("") == ""

