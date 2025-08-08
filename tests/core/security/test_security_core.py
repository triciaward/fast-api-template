import re
from datetime import timedelta

import pytest

pytestmark = pytest.mark.unit


def test_password_hash_and_verify():
    from app.core.security.security import get_password_hash, verify_password

    h = get_password_hash("Password123!")
    assert verify_password("Password123!", h) is True
    assert verify_password("wrong", h) is False


def test_refresh_token_hash_and_verify_and_fingerprint():
    from app.core.security.security import (
        create_refresh_token,
        fingerprint_refresh_token,
        hash_refresh_token,
        verify_refresh_token,
    )

    t = create_refresh_token()
    h = hash_refresh_token(t)
    assert verify_refresh_token(t, h) is True
    assert isinstance(fingerprint_refresh_token(t), str)
    assert len(fingerprint_refresh_token(t)) == 64


def test_api_key_generate_hash_verify_fingerprint():
    from app.core.security.security import (
        fingerprint_api_key,
        generate_api_key,
        hash_api_key,
        verify_api_key,
    )

    k = generate_api_key()
    assert k.startswith("sk_")
    assert re.match(r"^sk_[A-Za-z0-9_\-]+$", k)
    hk = hash_api_key(k)
    assert verify_api_key(k, hk) is True
    fp = fingerprint_api_key(k)
    assert len(fp) == 64


def test_create_access_token_contains_subject_and_exp():
    from jose import jwt

    from app.core.config.config import settings
    from app.core.security.security import create_access_token

    token = create_access_token("user1", expires_delta=timedelta(minutes=5))
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded["sub"] == "user1"
    assert "exp" in decoded
