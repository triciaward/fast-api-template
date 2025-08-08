import pytest

pytestmark = pytest.mark.unit


def test_create_helpers_cover_variants():
    from app.core.error_handling.error_handlers import (
        create_authentication_error,
        create_authorization_error,
        create_conflict_error,
        create_not_found_error,
        create_standardized_error,
        create_validation_error,
    )
    from app.schemas.core.errors import ErrorCode, ErrorType

    ed, sc = create_standardized_error(
        ErrorType.INTERNAL_SERVER_ERROR,
        "X",
        ErrorCode.INTERNAL_ERROR,
        503,
        {"a": 1},
    )
    assert sc == 503
    assert ed.type == ErrorType.INTERNAL_SERVER_ERROR
    assert ed.code == ErrorCode.INTERNAL_ERROR

    ed2, sc2 = create_validation_error(
        "bad",
        ErrorCode.INVALID_REQUEST,
        "field",
        "v",
        {"x": 1},
    )
    assert sc2 == 422
    assert ed2.type == ErrorType.VALIDATION_ERROR

    ed3, sc3 = create_authentication_error(
        "nope",
        ErrorCode.INVALID_CREDENTIALS,
        {"y": 2},
    )
    assert sc3 == 401
    assert ed3.type == ErrorType.AUTHENTICATION_ERROR

    ed4, sc4 = create_authorization_error(
        "denied",
        ErrorCode.INSUFFICIENT_PERMISSIONS,
        ["admin"],
        {"z": 3},
    )
    assert sc4 == 403
    assert ed4.type == ErrorType.AUTHORIZATION_ERROR

    ed5, sc5 = create_not_found_error(
        "missing",
        ErrorCode.RESOURCE_NOT_FOUND,
        "user",
        "1",
        {"q": 4},
    )
    assert sc5 == 404
    assert ed5.type == ErrorType.NOT_FOUND

    ed6, sc6 = create_conflict_error(
        "dup",
        ErrorCode.CONFLICT,
        "email",
        "e@x.com",
        {"w": 5},
    )
    assert sc6 == 409
    assert ed6.type == ErrorType.CONFLICT
