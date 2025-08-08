import types

import pytest

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_refresh_access_token_success(monkeypatch):
    from app.services.auth import refresh_token as svc

    async def fake_verify(db, token):
        return types.SimpleNamespace(user_id="uid")

    class DB:
        async def execute(self, *a, **k):
            class R:
                def scalar_one_or_none(self):
                    return types.SimpleNamespace(id="uid", is_deleted=False)

            return R()

    monkeypatch.setattr(svc, "verify_refresh_token_in_db", fake_verify)
    tok, exp = await svc.refresh_access_token(DB(), "raw")  # type: ignore[assignment]
    assert tok and exp


@pytest.mark.asyncio
async def test_revoke_all_sessions_with_except(monkeypatch):
    from app.services.auth import refresh_token as svc

    async def fake_get_by_hash(db, th):
        return types.SimpleNamespace(id="11111111-1111-1111-1111-111111111111")

    async def fake_revoke_all(db, uid):
        return 3

    def fake_hash(v):
        return "h"

    # Functions are exposed via app.crud in service module
    import app.crud as crud

    monkeypatch.setattr(crud, "get_refresh_token_by_hash", fake_get_by_hash)
    monkeypatch.setattr(crud, "revoke_all_user_sessions", fake_revoke_all)
    from app.core.security import security as sec

    monkeypatch.setattr(sec, "hash_refresh_token", fake_hash)

    n = await svc.revoke_all_sessions(types.SimpleNamespace(), types.SimpleNamespace(), except_token_value="x")  # type: ignore[arg-type]
    assert n == 3


def test_get_device_info_variants():
    from types import SimpleNamespace

    from app.services.auth.refresh_token import get_device_info

    req = SimpleNamespace(headers={"user-agent": "Mozilla/5.0 (Macintosh) Safari/605.1.15"})
    assert get_device_info(req) == "Safari on macOS"

    req2 = SimpleNamespace(headers={"user-agent": "Mozilla/5.0 (Windows NT 10.0) OtherBrowser"})
    assert get_device_info(req2) == "Other on Windows"

    req3 = SimpleNamespace(headers={"user-agent": "UnknownUA"})
    assert get_device_info(req3) == "Unknown Device"


def test_get_client_ip_and_cookie_helpers():
    from types import SimpleNamespace

    from app.services.auth.refresh_token import (
        get_client_ip,
        get_refresh_token_from_cookie,
    )

    req = SimpleNamespace(headers={"x-forwarded-for": "1.2.3.4, 5.6.7.8"}, client=SimpleNamespace(host="9.9.9.9"), cookies={})
    assert get_client_ip(req) == "1.2.3.4"

    req2 = SimpleNamespace(headers={}, client=None, cookies={})
    assert get_client_ip(req2) == "unknown"
    assert get_refresh_token_from_cookie(req2) is None


def test_get_device_info_linux_android_other_monkey():
    from types import SimpleNamespace

    from app.services.auth.refresh_token import get_device_info

    linux = SimpleNamespace(headers={"user-agent": "Mozilla/5.0 (X11; Linux x86_64) Firefox/120.0"})
    assert get_device_info(linux) == "Firefox on Linux"

    # UA includes Linux, so function classifies as Linux by order
    android = SimpleNamespace(headers={"user-agent": "Mozilla/5.0 (Linux; Android 14; Pixel) Chrome/120"})
    assert get_device_info(android) == "Chrome on Linux"

    android2 = SimpleNamespace(headers={"user-agent": "Mozilla/5.0 (Android 14; Pixel) Safari/605"})
    assert get_device_info(android2) == "Safari on Android"

    other = SimpleNamespace(headers={"user-agent": "Mozilla/5.0 (Something) UnknownBrowser/1.0"})
    assert get_device_info(other) == "Other on Other"


@pytest.mark.asyncio
async def test_revoke_all_sessions_without_except(monkeypatch):
    import app.crud as crud
    from app.services.auth import refresh_token as svc

    async def fake_revoke_all(db, uid):
        return 5

    monkeypatch.setattr(crud, "revoke_all_user_sessions", fake_revoke_all)
    n = await svc.revoke_all_sessions(types.SimpleNamespace(), "11111111-1111-1111-1111-111111111111")  # type: ignore[arg-type]
    assert n == 5


@pytest.mark.asyncio
async def test_revoke_all_sessions_with_except_token_not_found(monkeypatch):
    import app.crud as crud
    from app.services.auth import refresh_token as svc

    async def fake_get_by_hash(db, th):
        return None

    async def fake_revoke_all(db, uid):
        return 7

    from app.core.security import security as sec

    def fake_hash(v):
        return "hashed"

    monkeypatch.setattr(crud, "get_refresh_token_by_hash", fake_get_by_hash)
    monkeypatch.setattr(crud, "revoke_all_user_sessions", fake_revoke_all)
    monkeypatch.setattr(sec, "hash_refresh_token", fake_hash)

    n = await svc.revoke_all_sessions(types.SimpleNamespace(), "11111111-1111-1111-1111-111111111111", except_token_value="raw")  # type: ignore[arg-type]
    assert n == 7


