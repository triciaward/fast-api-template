import pytest

from app.models.auth.user import User

pytestmark = pytest.mark.template_only

def test_user_model_has_email_field() -> None:
    assert hasattr(User, "email")
