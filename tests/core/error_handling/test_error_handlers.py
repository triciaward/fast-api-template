import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.core.error_handling.error_handlers import register_error_handlers


def _make_app():
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/err/401")
    def err401():  # type: ignore[no-untyped-def]
        raise HTTPException(status_code=401, detail="Invalid email or password")

    @app.get("/err/403")
    def err403():  # type: ignore[no-untyped-def]
        raise HTTPException(status_code=403, detail="Superuser privileges required")

    @app.get("/err/404")
    def err404():  # type: ignore[no-untyped-def]
        raise HTTPException(status_code=404, detail="User not found")

    @app.get("/err/422")
    def err422():  # type: ignore[no-untyped-def]
        raise HTTPException(status_code=422, detail="Invalid request")

    return app


def test_http_exception_mapped_to_standard_error():
    app = _make_app()
    client = TestClient(app)

    r401 = client.get("/err/401")
    assert r401.status_code == 401
    assert r401.json()["error"]["code"] in {"invalid_credentials", "token_invalid"}

    r403 = client.get("/err/403")
    assert r403.status_code == 403
    assert r403.json()["error"]["code"] == "superuser_required"

    r404 = client.get("/err/404")
    assert r404.status_code == 404
    assert r404.json()["error"]["code"] in {"user_not_found", "resource_not_found"}

    r422 = client.get("/err/422")
    assert r422.status_code == 422
    assert r422.json()["error"]["type"] == "ValidationError"


def test_integrity_error_mapping_conflict():
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/err/integrity")
    def err_integrity():  # type: ignore[no-untyped-def]
        # Simulate duplicate email
        raise IntegrityError(
            'duplicate key value violates unique constraint "users_email_key"',
            None,
            None,
        )

    client = TestClient(app)
    r = client.get("/err/integrity")
    assert r.status_code == 409
    body = r.json()
    assert body["error"]["code"] in {
        "email_already_exists",
        "username_already_exists",
        "conflict",
    }


pytestmark = pytest.mark.template_only


def test_stub_error_handlers() -> None:
    assert True
