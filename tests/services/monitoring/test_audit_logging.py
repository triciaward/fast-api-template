import types

import pytest

pytestmark = pytest.mark.unit


class DummyRequest:
    def __init__(self):
        self.headers = {"User-Agent": "pytest", "X-Forwarded-For": "1.2.3.4"}
        self.client = types.SimpleNamespace(host="5.6.7.8")
        self.url = types.SimpleNamespace(path="/x")
        self.method = "GET"


@pytest.mark.asyncio
async def test_log_login_attempt_calls_create_audit_log(monkeypatch):
    from app.services.monitoring import audit as mod

    captured = {}

    async def fake_create_audit_log(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return types.SimpleNamespace(id="aaaa-bbbb")

    monkeypatch.setattr(mod, "create_audit_log", fake_create_audit_log)

    req = DummyRequest()
    user = types.SimpleNamespace(id="u1")
    await mod.log_login_attempt(db=object(), request=req, user=user, success=False)

    assert captured["event_type"] == "login_failed"
    assert captured["user_id"] == "u1"
    assert captured["ip_address"] == "1.2.3.4"
    assert captured["user_agent"] == "pytest"


@pytest.mark.asyncio
async def test_log_api_key_usage_records_context(monkeypatch):
    from app.services.monitoring import audit as mod

    captured = {}

    async def fake_create_audit_log(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return types.SimpleNamespace(id="cccc-dddd")

    monkeypatch.setattr(mod, "create_audit_log", fake_create_audit_log)

    req = DummyRequest()
    await mod.log_api_key_usage(
        db=object(),
        request=req,
        api_key_id="kid",
        key_label="label",
        user_id="u2",
        endpoint_path="/custom",
        http_method="POST",
    )

    assert captured["event_type"] == "api_key_usage"
    assert captured["context"]["api_key_id"] == "kid"
    assert captured["context"]["key_label"] == "label"
    assert captured["context"]["endpoint_path"] == "/custom"
    assert captured["context"]["http_method"] == "POST"
    assert captured["success"] is True
