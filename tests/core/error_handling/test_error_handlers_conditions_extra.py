import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


def _app_with_handlers() -> FastAPI:
    app = FastAPI()
    from app.core.error_handling.error_handlers import register_error_handlers

    register_error_handlers(app)
    return app


def test_http_exception_detail_dict_without_message_uses_str():
    app = _app_with_handlers()

    @app.get("/dict-no-message")
    def route():  # type: ignore[no-untyped-def]
        raise HTTPException(status_code=422, detail={"foo": "bar"})

    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/dict-no-message")
    assert r.status_code == 422
    body = r.json()
    assert body["error"]["type"] == "ValidationError"
    # Message falls back to str(dict)
    assert body["error"]["message"].startswith("{")


def test_http_exception_custom_rate_limit_detail():
    from app.core.error_handling.exceptions import RateLimitError

    app = _app_with_handlers()

    @app.get("/rl")
    def route():  # type: ignore[no-untyped-def]
        raise RateLimitError(message="Too fast", retry_after=5)

    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/rl")
    assert r.status_code == 429
    body = r.json()
    assert body["error"]["type"] == "RateLimitExceeded"
    assert body["error"]["message"] == "Too fast"
    assert body["error"]["details"]["retry_after"] == 5


def test_http_exception_custom_internal_server_error_detail():
    from app.core.error_handling.exceptions import ConfigurationError

    app = _app_with_handlers()

    @app.get("/cfg")
    def route():  # type: ignore[no-untyped-def]
        raise ConfigurationError(message="Bad cfg", config_key="X")

    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/cfg")
    assert r.status_code == 500
    body = r.json()
    assert body["error"]["type"] == "InternalServerError"
    assert body["error"]["message"] == "Bad cfg"


def test_http_exception_custom_unhandled_type_falls_back_to_generic():
    from app.core.error_handling.exceptions import ExternalServiceError

    app = _app_with_handlers()

    @app.get("/svc")
    def route():  # type: ignore[no-untyped-def]
        raise ExternalServiceError(message="Down", service_name="mail")

    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/svc")
    assert r.status_code == 502
    body = r.json()
    # Falls back to generic ErrorDetail with SERVICE_UNAVAILABLE type
    assert body["error"]["type"] == "ServiceUnavailable"
    assert body["error"]["message"] == "Down"


def test_validation_exception_bytes_value_gets_decoded(monkeypatch):
    # Directly raise a RequestValidationError with a bytes input to exercise decoding
    from fastapi.exceptions import RequestValidationError

    app = _app_with_handlers()

    @app.get("/bytes")
    def route():  # type: ignore[no-untyped-def]
        raise RequestValidationError(
            [
                {
                    "loc": ("query", "content"),
                    "msg": "Invalid",
                    "type": "value_error",
                    "input": b"\xff\xfe\xfd",
                },
            ],
        )

    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/bytes")
    assert r.status_code == 422
    body = r.json()
    assert body["error"]["type"] == "ValidationError"
    assert "errors" in body["error"]["details"]
