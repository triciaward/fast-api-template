import pytest

from app.core.config.config import settings

pytestmark = pytest.mark.template_only


def test_cors_origins_list_is_list() -> None:
    assert isinstance(settings.cors_origins_list, list)
