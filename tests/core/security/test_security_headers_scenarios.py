import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


def _app():
    app = FastAPI()
    from app.core.security.security_headers import configure_security_headers

    configure_security_headers(app)

    @app.get("/docs")
    def docs():  # type: ignore[no-untyped-def]
        return {"ok": True}

    @app.post("/api/v1/auth/login")
    def login():  # type: ignore[no-untyped-def]
        return {"ok": True}

    return app


def test_headers_set_and_csp_varies():
    app = _app()
    client = TestClient(app)
    r = client.get("/docs")
    assert r.headers["Content-Security-Policy"].startswith(
        "default-src 'self'; script-src 'self' 'unsafe-inline'",
    )
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    r2 = client.post("/api/v1/auth/login")
    assert r2.headers["Content-Security-Policy"].startswith(
        "default-src 'self'; script-src 'self'",
    )
    assert r2.headers["Cache-Control"].startswith("no-store")
