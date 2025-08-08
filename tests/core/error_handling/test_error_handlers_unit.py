import types

import pytest
from starlette.requests import Request

pytestmark = pytest.mark.unit


def _make_request(headers: dict[str, str] | None = None, path: str = "/x") -> Request:
    headers_list = []
    if headers:
        headers_list = [(k.lower().encode(), v.encode()) for k, v in headers.items()]
    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "headers": headers_list,
        "query_string": b"",
    }
    return Request(scope)


def test_get_request_id_header_and_generated():
    from app.core.error_handling.error_handlers import get_request_id

    r1 = _make_request({"X-Request-ID": "req-123"})
    assert get_request_id(r1) == "req-123"

    r2 = _make_request()
    rid = get_request_id(r2)
    assert isinstance(rid, str) and len(rid) > 10


@pytest.mark.asyncio
async def test_integrity_error_handler_email_username_and_generic():
    from sqlalchemy.exc import IntegrityError

    from app.core.error_handling.error_handlers import integrity_error_handler

    req = _make_request()

    # Email duplicate
    err_email = IntegrityError("INSERT", None, Exception("duplicate key email"))
    resp = await integrity_error_handler(req, err_email)
    assert resp.status_code == 409

    # Username duplicate
    err_user = IntegrityError("INSERT", None, Exception("duplicate key username"))
    resp = await integrity_error_handler(req, err_user)
    assert resp.status_code == 409

    # Generic constraint
    err_other = IntegrityError("INSERT", None, Exception("some other constraint"))
    resp = await integrity_error_handler(req, err_other)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_rate_limit_exception_handler_ducktyped():
    from app.core.error_handling.error_handlers import rate_limit_exception_handler

    req = _make_request()
    exc = types.SimpleNamespace(retry_after=30, limit=5)
    resp = await rate_limit_exception_handler(req, exc)  # type: ignore[arg-type]
    assert resp.status_code == 429

