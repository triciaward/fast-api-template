import pytest

pytestmark = pytest.mark.unit


def test_get_device_info_firefox_and_ios():
    from app.services.auth.refresh_token import get_device_info

    class Req:
        def __init__(self, ua):
            self.headers = {"user-agent": ua}

    s1 = get_device_info(Req("Mozilla/5.0 Firefox iPhone"))
    assert s1 == "Firefox on iOS"


def test_get_client_ip_no_headers():
    from app.services.auth.refresh_token import get_client_ip

    class R:
        def __init__(self):
            self.headers = {}
            self.client = None

    assert get_client_ip(R()) == "unknown"
