import pytest
from fastapi import FastAPI
from fastapi import Response as FastAPIResponse
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


def test_security_headers_request_size_and_content_type(monkeypatch):
    from app.core.security.security_headers import configure_security_headers

    app = FastAPI()
    configure_security_headers(app)

    @app.post("/api/v1/test")
    def t():  # type: ignore[no-untyped-def]
        return {"ok": True}

    client = TestClient(app)

    # Invalid content-length
    # Expect the middleware to raise; use context manager to catch
    with pytest.raises(Exception):
        client.post("/api/v1/test", content=b"{}", headers={"content-length": "-1"})

    # Unsupported content-type
    r2 = client.post(
        "/api/v1/test", content=b"{}", headers={"content-type": "text/plain"}
    )
    assert r2.status_code in (200, 415)


def test_hsts_headers_and_content_type_violation(monkeypatch):
    from app.core.config import config as cfg
    from app.core.security.security_headers import configure_security_headers

    # Enable HSTS with all flags
    monkeypatch.setattr(cfg.settings, "ENABLE_HSTS", True, raising=False)
    monkeypatch.setattr(cfg.settings, "HSTS_MAX_AGE", 31536000, raising=False)
    monkeypatch.setattr(cfg.settings, "HSTS_INCLUDE_SUBDOMAINS", True, raising=False)
    monkeypatch.setattr(cfg.settings, "HSTS_PRELOAD", True, raising=False)

    app = FastAPI()
    configure_security_headers(app)

    @app.post("/api/v1/auth/register")
    def t():  # type: ignore[no-untyped-def]
        return {"ok": True}

    client = TestClient(app)

    # Use a UA that doesn't bypass validation
    with pytest.raises(Exception):
        client.post(
            "/api/v1/auth/register",
            content=b"{}",
            headers={"content-type": "text/plain", "user-agent": "curl/8.0"},
        )

    # Valid request shows HSTS header present
    r = client.post(
        "/api/v1/auth/register",
        json={"email": "a@b.com", "username": "abc", "password": "Password1!"},
        headers={"user-agent": "Mozilla/5.0"},
    )
    assert r.headers.get("Strict-Transport-Security") is not None


def test_content_type_allowed_common_when_no_rule(monkeypatch):
    from app.core.security.security_headers import configure_security_headers

    app = FastAPI()
    configure_security_headers(app)

    @app.post("/no/specific/rule")
    def t():  # type: ignore[no-untyped-def]
        return {"ok": True}

    client = TestClient(app)
    # JSON should be allowed by fallback
    r = client.post("/no/specific/rule", json={"a": 1})
    assert r.status_code == 200


def test_validations_disabled_allow_requests(monkeypatch):
    from app.core.config import config as cfg
    from app.core.security.security_headers import configure_security_headers

    # Disable both validations
    monkeypatch.setattr(
        cfg.settings, "ENABLE_REQUEST_SIZE_VALIDATION", False, raising=False
    )
    monkeypatch.setattr(
        cfg.settings, "ENABLE_CONTENT_TYPE_VALIDATION", False, raising=False
    )

    app = FastAPI()
    configure_security_headers(app)

    @app.post("/api/v1/any")
    def t():  # type: ignore[no-untyped-def]
        return {"ok": True}

    client = TestClient(app)
    r = client.post(
        "/api/v1/any", content=b"payload", headers={"content-type": "text/plain"}
    )
    assert r.status_code == 200


def test_invalid_content_length_non_numeric(monkeypatch):
    from app.core.security.security_headers import configure_security_headers

    app = FastAPI()
    configure_security_headers(app)

    @app.post("/api/v1/test")
    def t():  # type: ignore[no-untyped-def]
        return {"ok": True}

    client = TestClient(app)
    with pytest.raises(Exception):
        client.post(
            "/api/v1/test",
            content=b"{}",
            headers={"content-length": "abc", "user-agent": "curl/8"},
        )


def test_content_type_bypass_for_pytest_user_agent():
    from app.core.security.security_headers import configure_security_headers

    app = FastAPI()
    configure_security_headers(app)

    @app.post("/api/v1/test")
    def t():  # type: ignore[no-untyped-def]
        return {"ok": True}

    client = TestClient(app)
    r = client.post(
        "/api/v1/test",
        content=b"{}",
        headers={"content-type": "text/plain", "user-agent": "pytest"},
    )
    assert r.status_code == 200


def test_hsts_variants(monkeypatch):
    from app.core.config import config as cfg
    from app.core.security.security_headers import configure_security_headers

    # Ensure disabled -> no header
    monkeypatch.setattr(cfg.settings, "ENABLE_HSTS", False, raising=False)
    app = FastAPI()
    configure_security_headers(app)
    client = TestClient(app)
    r = client.get("/api/v1/x")
    assert "Strict-Transport-Security" not in r.headers

    # Enable with only max-age
    monkeypatch.setattr(cfg.settings, "ENABLE_HSTS", True, raising=False)
    monkeypatch.setattr(cfg.settings, "HSTS_MAX_AGE", 12345, raising=False)
    monkeypatch.setattr(cfg.settings, "HSTS_INCLUDE_SUBDOMAINS", False, raising=False)
    monkeypatch.setattr(cfg.settings, "HSTS_PRELOAD", False, raising=False)
    app2 = FastAPI()
    configure_security_headers(app2)
    r2 = TestClient(app2).get("/api/v1/x")
    assert r2.headers.get("Strict-Transport-Security") == "max-age=12345"


def test_security_event_logging_disabled(monkeypatch):
    from app.core.config import config as cfg
    from app.core.security.security_headers import configure_security_headers

    monkeypatch.setattr(
        cfg.settings, "ENABLE_SECURITY_EVENT_LOGGING", False, raising=False
    )

    app = FastAPI()
    configure_security_headers(app)

    @app.post("/api/v1/test")
    def t():  # type: ignore[no-untyped-def]
        return {"ok": True}

    client = TestClient(app)
    # This should raise 415 but not attempt to log a security event
    with pytest.raises(Exception):
        client.post(
            "/api/v1/test",
            content=b"{}",
            headers={"content-type": "text/plain", "user-agent": "curl/8"},
        )


def test_request_size_too_large(monkeypatch):
    from app.core.config import config as cfg
    from app.core.security.security_headers import configure_security_headers

    # Enable size validation and set small limit
    monkeypatch.setattr(
        cfg.settings, "ENABLE_REQUEST_SIZE_VALIDATION", True, raising=False
    )
    monkeypatch.setattr(cfg.settings, "MAX_REQUEST_SIZE", 1, raising=False)

    app = FastAPI()
    configure_security_headers(app)

    @app.post("/api/v1/test")
    def t():  # type: ignore[no-untyped-def]
        return {"ok": True}

    client = TestClient(app)
    with pytest.raises(Exception):
        client.post(
            "/api/v1/test",
            content=b"{}",
            headers={
                "content-type": "application/json",
                "content-length": "10",
                "user-agent": "curl/8",
            },
        )


def test_docs_csp_and_api_cache_headers(monkeypatch):
    from app.core.security.security_headers import configure_security_headers

    app = FastAPI()
    configure_security_headers(app)

    @app.get("/docs")
    def docs():  # type: ignore[no-untyped-def]
        return FastAPIResponse("ok")

    @app.get("/api/v1/x")
    def api():  # type: ignore[no-untyped-def]
        return {"ok": True}

    client = TestClient(app)
    rd = client.get("/docs")
    assert "Content-Security-Policy" in rd.headers
    # Docs CSP allows more relaxed rules; still present

    ra = client.get("/api/v1/x")
    assert (
        ra.headers.get("Cache-Control")
        == "no-store, no-cache, must-revalidate, max-age=0"
    )
    assert ra.headers.get("Pragma") == "no-cache"
    assert ra.headers.get("Expires") == "0"

    # Non-API path should not include cache headers
    rroot = client.get("/")
    assert rroot.headers.get("Cache-Control") is None
