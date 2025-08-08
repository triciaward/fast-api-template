import types

import pytest

pytestmark = pytest.mark.unit


def test_get_device_info_variants():
    from app.services.auth.refresh_token import get_device_info

    class Req:
        def __init__(self, ua):
            self.headers = {"user-agent": ua}

    assert get_device_info(Req("Mozilla/5.0 Chrome on Windows")) == "Chrome on Windows"
    assert get_device_info(Req("Something Else")) == "Unknown Device"


def test_get_client_ip_variants():
    from app.services.auth.refresh_token import get_client_ip

    class R:
        def __init__(self, h=None, real=None, client=None):
            self.headers = {}
            if h:
                self.headers["x-forwarded-for"] = h
            if real:
                self.headers["x-real-ip"] = real
            self.client = client

    assert get_client_ip(R(h="1.2.3.4, 5.6.7.8")) == "1.2.3.4"
    assert get_client_ip(R(real="9.9.9.9")) == "9.9.9.9"
    assert get_client_ip(R(client=types.SimpleNamespace(host="7.7.7.7"))) == "7.7.7.7"


def test_cookie_helpers(monkeypatch):
    from app.services.auth.refresh_token import (
        clear_refresh_token_cookie,
        set_refresh_token_cookie,
    )

    class Resp:
        def __init__(self):
            self.cookies = {}

        def set_cookie(self, key, value, **kwargs):
            self.cookies[key] = value

        def delete_cookie(self, key, **kwargs):
            self.cookies.pop(key, None)

    r = Resp()
    set_refresh_token_cookie(r, "abc")
    assert r.cookies
    clear_refresh_token_cookie(r)
    assert not r.cookies
