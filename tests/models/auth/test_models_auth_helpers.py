import datetime as dt
import uuid

import pytest

pytestmark = pytest.mark.unit


def test_api_key_helpers_and_repr():
    from app.models.auth.api_key import APIKey

    k = APIKey()
    k.id = uuid.uuid4()
    k.user_id = None
    k.label = "svc"
    k.scopes = ["read", "write"]
    k.is_active = True
    k.expires_at = None
    k.is_deleted = False  # type: ignore[attr-defined]

    assert k.is_system_key is True
    assert k.is_expired is False and k.is_valid is True
    assert k.has_scope("read") is True
    assert k.has_any_scope(["admin", "read"]) is True
    assert k.has_all_scopes(["read", "write"]) is True

    # Revoke flips validity
    k.revoke()
    assert k.is_active is False and k.is_valid is False
    assert "APIKey(" in repr(k)


def test_refresh_token_helpers_and_repr(monkeypatch):
    from app.models.auth.refresh_token import RefreshToken
    from app.utils import datetime_utils as du

    now = dt.datetime.now(dt.timezone.utc)
    monkeypatch.setattr(du, "utc_now", lambda: now)

    t = RefreshToken()
    t.id = uuid.uuid4()
    t.user_id = uuid.uuid4()
    t.token_hash = "h"
    t.expires_at = now + dt.timedelta(hours=2)
    t.is_revoked = False
    t.is_deleted = False  # type: ignore[attr-defined]

    assert t.is_expired is False and t.is_valid is True and t.is_active is True
    assert t.time_until_expiry is not None and t.time_until_expiry > 0
    # 2 hours < 24 hours threshold -> near expiry
    assert t.is_near_expiry is True

    # Device summary
    assert t.get_device_summary() == "Unknown device"
    t.device_info = "Mozilla/5.0 (Windows) Chrome/120"
    assert t.get_device_summary() == "Chrome"

    # Revoke flips validity and updates timestamp
    monkeypatch.setattr(du, "utc_now", lambda: now + dt.timedelta(hours=3))
    t.revoke()
    assert t.is_valid is False
    assert isinstance(t.updated_at, dt.datetime)
    assert "RefreshToken(" in repr(t)
