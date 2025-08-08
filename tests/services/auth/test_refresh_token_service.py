import types

import pytest

from app.core.config.config import settings
from app.services.auth import refresh_token as rt

pytestmark = pytest.mark.unit


def test_set_refresh_token_cookie_flags() -> None:
    class DummyResponse:
        def __init__(self) -> None:
            self.cookies: dict[str, dict[str, str]] = {}

        def set_cookie(self, **kwargs):  # type: ignore[no-untyped-def]
            self.cookies[kwargs["key"]] = kwargs  # type: ignore[index]

    resp = DummyResponse()
    rt.set_refresh_token_cookie(resp, "abc123")  # type: ignore[arg-type]

    c = resp.cookies[settings.REFRESH_TOKEN_COOKIE_NAME]
    assert c["httponly"] is settings.REFRESH_TOKEN_COOKIE_HTTPONLY
    assert c["secure"] is settings.REFRESH_TOKEN_COOKIE_SECURE
    assert c["path"] == settings.REFRESH_TOKEN_COOKIE_PATH
    assert c["samesite"] == settings.REFRESH_TOKEN_COOKIE_SAMESITE


def test_get_client_ip_headers_precedence() -> None:
    request = types.SimpleNamespace(
        headers={"x-forwarded-for": "1.2.3.4, 5.6.7.8", "x-real-ip": "9.9.9.9"},
        client=types.SimpleNamespace(host="10.0.0.1"),
    )
    assert rt.get_client_ip(request) == "1.2.3.4"  # type: ignore[arg-type]

    request2 = types.SimpleNamespace(headers={"x-real-ip": "9.9.9.9"}, client=None)
    assert rt.get_client_ip(request2) == "9.9.9.9"  # type: ignore[arg-type]

    request3 = types.SimpleNamespace(
        headers={}, client=types.SimpleNamespace(host="10.0.0.1")
    )
    assert rt.get_client_ip(request3) == "10.0.0.1"  # type: ignore[arg-type]
