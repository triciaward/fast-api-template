import types

import pytest

pytestmark = pytest.mark.unit


class DummyRequest:
    def __init__(self, forwarded: str | None = None, real: str | None = None):
        self.headers = {"User-Agent": "pytest"}
        if forwarded:
            self.headers["X-Forwarded-For"] = forwarded
        if real:
            self.headers["X-Real-IP"] = real
        self.client = types.SimpleNamespace(host="9.9.9.9")
        self.url = types.SimpleNamespace(path="/x")
        self.method = "GET"


@pytest.mark.asyncio
async def test_log_logout_and_password_change(monkeypatch):
    from app.services.monitoring import audit as mod

    ids = []

    async def fake_create_audit_log(**kwargs):  # type: ignore[no-untyped-def]
        ids.append("ok")
        return types.SimpleNamespace(id="aaaa")

    monkeypatch.setattr(mod, "create_audit_log", fake_create_audit_log)

    req = DummyRequest()
    user = types.SimpleNamespace(id="u1")

    await mod.log_logout(db=object(), request=req, user=user)
    await mod.log_password_change(
        db=object(),
        request=req,
        user=user,
        change_type="password_change",
    )

    assert len(ids) == 2


@pytest.mark.asyncio
async def test_log_account_deletion_and_email_verification(monkeypatch):
    from app.services.monitoring import audit as mod

    events = []

    async def fake_create_audit_log(event_type: str, **kwargs):  # type: ignore[no-untyped-def]
        events.append(event_type)
        return types.SimpleNamespace(id="bbbb")

    monkeypatch.setattr(mod, "create_audit_log", fake_create_audit_log)

    req = DummyRequest(real="1.1.1.1")
    user = types.SimpleNamespace(id="u2")

    await mod.log_account_deletion(
        db=object(),
        request=req,
        user=user,
        deletion_stage="requested",
    )
    await mod.log_email_verification(db=object(), request=req, user=user, success=False)

    assert "account_deletion" in events and "email_verification" in events


@pytest.mark.asyncio
async def test_log_oauth_login(monkeypatch):
    from app.services.monitoring import audit as mod

    captured = {}

    async def fake_create_audit_log(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return types.SimpleNamespace(id="cccc")

    monkeypatch.setattr(mod, "create_audit_log", fake_create_audit_log)

    req = DummyRequest()
    user = types.SimpleNamespace(id="u3")

    await mod.log_oauth_login(
        db=object(),
        request=req,
        user=user,
        oauth_provider="google",
        success=True,
    )

    assert captured["event_type"] == "oauth_login"
    assert captured["context"]["oauth_provider"] == "google"
