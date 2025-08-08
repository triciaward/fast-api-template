import pytest

pytestmark = pytest.mark.unit


def test_admin_bulk_operation_request_validator_allows_and_rejects():
    import uuid

    from app.schemas.admin.admin import AdminBulkOperationRequest

    # Allowed operation normalizes to lowercase
    req = AdminBulkOperationRequest(user_ids=[uuid.uuid4()], operation="Verify")  # type: ignore[arg-type]
    assert req.operation == "verify"

    # Invalid operation raises with allowed list in message
    with pytest.raises(ValueError) as ei:
        AdminBulkOperationRequest(user_ids=[uuid.uuid4()], operation="foo")  # type: ignore[arg-type]
    assert "Invalid operation" in str(ei.value)


def test_admin_user_create_validators():
    from app.schemas.admin.admin import AdminUserCreate

    ok = AdminUserCreate(
        email=" USER@EX.com ", username=" user_name ", password="Password123!",
    )
    assert ok.email == "user@ex.com"

    with pytest.raises(ValueError):
        AdminUserCreate(email="bad", username="user", password="Password123!")
