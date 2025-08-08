import pytest

pytestmark = pytest.mark.unit


def test_exception_constructors_and_fields():
    from app.core.error_handling.exceptions import (
        AuthenticationError,
        AuthorizationError,
        BusinessLogicError,
        ConfigurationError,
        ConflictError,
        DatabaseError,
        RateLimitError,
        ResourceNotFoundError,
        ValidationError,
    )
    from app.schemas.core.errors import ErrorCode, ErrorType

    v = ValidationError("bad", code=ErrorCode.INVALID_REQUEST, field="email", value="X")
    assert v.status_code == 422 and v.error_type == ErrorType.VALIDATION_ERROR
    assert v.error_details["field"] == "email"

    a1 = AuthenticationError()
    assert a1.status_code == 401 and a1.error_code == ErrorCode.INVALID_CREDENTIALS

    a2 = AuthorizationError(required_permissions=["admin"])  # type: ignore[arg-type]
    assert a2.status_code == 403 and "required_permissions" in a2.error_details

    n = ResourceNotFoundError("missing", resource_type="user", resource_id="1")
    assert n.status_code == 404 and n.error_code == ErrorCode.RESOURCE_NOT_FOUND

    c = ConflictError("dupe", conflicting_field="email", conflicting_value="e@x.com")
    assert c.status_code == 409 and c.error_type == ErrorType.CONFLICT

    r = RateLimitError(retry_after=10)
    assert r.status_code == 429 and r.error_details["retry_after"] == 10

    d = DatabaseError(operation="insert")
    assert d.status_code == 500 and d.error_type == ErrorType.DATABASE_ERROR

    cfg = ConfigurationError("bad cfg", config_key="X")
    assert cfg.status_code == 500 and cfg.error_code == ErrorCode.INTERNAL_ERROR

    b = BusinessLogicError("rule", business_rule="must_be_unique")
    assert b.status_code == 400 and b.error_type == ErrorType.VALIDATION_ERROR


def test_helper_raisers_map_to_exceptions():
    from app.core.error_handling.exceptions import (
        ValidationException,
        raise_authentication_error,
        raise_authorization_error,
        raise_conflict_error,
        raise_not_found_error,
        raise_rate_limit_error,
        raise_validation_error,
    )

    with pytest.raises(ValidationException):
        raise_validation_error("bad", field="email", value="x")

    with pytest.raises(Exception) as ei1:
        raise_not_found_error("missing", resource_type="u", resource_id="1")
    assert ei1.value.status_code == 404

    with pytest.raises(Exception) as ei2:
        raise_conflict_error("dupe", conflicting_field="email", conflicting_value="x")
    assert ei2.value.status_code == 409

    with pytest.raises(Exception) as ei3:
        raise_rate_limit_error(retry_after=5)
    assert ei3.value.status_code == 429

    with pytest.raises(Exception) as ei4:
        raise_authentication_error()
    assert ei4.value.status_code == 401

    with pytest.raises(Exception) as ei5:
        raise_authorization_error()
    assert ei5.value.status_code == 403


