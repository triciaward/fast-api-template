import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError

pytestmark = pytest.mark.unit


def _app_with_route(raises):
    app = FastAPI()

    @app.get("/boom")
    def boom():  # type: ignore[no-untyped-def]
        raise raises

    # Install template's error handlers
    from app.core.error_handling.error_handlers import register_error_handlers

    register_error_handlers(app)
    return app


def test_integrity_error_mapped_to_400():
    err = IntegrityError("INSERT", params=None, orig=Exception("duplicate key"))
    app = _app_with_route(err)
    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/boom")
    # Template maps IntegrityError to 409 Conflict
    assert r.status_code == 409
    assert r.json()["error"]["type"] in {"Conflict", "IntegrityError", "BadRequest"}


def test_operational_error_mapped_to_503():
    err = OperationalError("SELECT", params=None, orig=Exception("db down"))
    app = _app_with_route(err)
    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/boom")
    # General SQLAlchemy errors map to 500 in template
    assert r.status_code == 500


def test_dbapi_error_mapped_to_500():
    err = DBAPIError("SELECT", params=None, orig=Exception("dbapi"))
    app = _app_with_route(err)
    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/boom")
    assert r.status_code == 500


