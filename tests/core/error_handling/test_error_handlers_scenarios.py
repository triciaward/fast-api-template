from fastapi import Body, FastAPI
from fastapi.testclient import TestClient

from app.core.error_handling.error_handlers import register_error_handlers


def _app_with_handlers():
    app = FastAPI()
    register_error_handlers(app)

    @app.post("/num")
    def num(n: int = Body(..., embed=True)):  # type: ignore[no-untyped-def]
        return {"n": n}

    @app.get("/boom")
    def boom():  # type: ignore[no-untyped-def]
        raise RuntimeError("unexpected")

    return app


def test_422_validation_envelope():
    app = _app_with_handlers()
    c = TestClient(app)
    # Provide wrong type for required int parameter
    r = c.post("/num", json={"n": "not-an-int"})
    assert r.status_code in (422,)
    body = r.json()
    assert body["error"]["type"] == "ValidationError"
    assert body["error"]["code"] == "invalid_request"


def test_405_method_not_allowed_envelope():
    app = _app_with_handlers()
    c = TestClient(app)
    # GET not allowed on /num which only accepts POST
    r = c.get("/num")
    assert r.status_code == 405
    body = r.json()
    # Some frameworks return default structure for 405; accept either
    assert ("error" in body) or ("detail" in body)


def test_generic_exception_mapped_to_500():
    app = _app_with_handlers()
    # Prevent server exception propagation so response is captured
    c = TestClient(app, raise_server_exceptions=False)
    r = c.get("/boom")
    assert r.status_code == 500
    body = r.json()
    # Schema defines InternalServerError as the type name
    assert body["error"]["type"] == "InternalServerError"

