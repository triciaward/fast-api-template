import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


def _app_with_handler(detail: str, status_code: int):
    app = FastAPI()

    @app.get("/boom")
    def boom():  # type: ignore[no-untyped-def]
        raise HTTPException(status_code=status_code, detail=detail)

    from app.core.error_handling.error_handlers import register_error_handlers

    register_error_handlers(app)
    return app


@pytest.mark.parametrize(
    "status_code,detail,etype",
    [
        (401, "Not authenticated", "AuthenticationError"),
        (403, "Forbidden", "AuthorizationError"),
        (404, "Not Found", "NotFound"),
        (409, "Conflict", "Conflict"),
        (422, {"message": "Invalid", "field": "x"}, "ValidationError"),
    ],
)
def test_http_exception_mapping(status_code, detail, etype):
    app = _app_with_handler(detail, status_code)
    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/boom")
    assert r.status_code == status_code
    body = r.json()
    assert body["error"]["type"].startswith(etype)

