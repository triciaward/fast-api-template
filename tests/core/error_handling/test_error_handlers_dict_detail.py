import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


def test_http_exception_detail_dict_message_and_code():
    app = FastAPI()

    @app.get("/boom")
    def boom():  # type: ignore[no-untyped-def]
        raise HTTPException(status_code=422, detail={"message": "Bad", "extra": 1})

    from app.core.error_handling.error_handlers import register_error_handlers

    register_error_handlers(app)
    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/boom")
    assert r.status_code == 422
    body = r.json()
    assert body["error"]["type"] == "ValidationError"
    assert body["error"]["message"] == "Bad"
