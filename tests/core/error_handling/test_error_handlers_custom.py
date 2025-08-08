import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


def _app_with_custom(exc):
    app = FastAPI()

    @app.get("/custom")
    def custom():  # type: ignore[no-untyped-def]
        raise exc

    from app.core.error_handling.error_handlers import register_error_handlers

    register_error_handlers(app)
    return app


def test_custom_authentication_exception_envelope():
    from app.core.error_handling.exceptions import AuthenticationException

    # Provide a valid ErrorCode string
    exc = AuthenticationException(message="Nope")
    app = _app_with_custom(exc)
    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/custom")
    assert r.status_code == 401
    body = r.json()
    assert body["error"]["type"] == "AuthenticationError"
    assert "Nope" in body["error"]["message"]


def test_custom_validation_exception_envelope():
    from app.core.error_handling.exceptions import ValidationException
    exc = ValidationException(message="Bad thing", field="email", value="x")
    app = _app_with_custom(exc)
    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/custom")
    assert r.status_code == 422
    body = r.json()
    assert body["error"]["type"] == "ValidationError"
    assert body["error"]["details"]["field"] == "email"

