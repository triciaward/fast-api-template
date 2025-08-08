import pytest

pytestmark = pytest.mark.unit


def test_field_filter_operators_basic():
    from app.models import User
    from app.utils.search_filter import (
        FilterOperator,
        SearchFilterBuilder,
        SearchFilterConfig,
        create_field_filter,
    )

    b = SearchFilterBuilder(User)
    cfg = SearchFilterConfig(
        filters=[
            create_field_filter("is_superuser", FilterOperator.EQUALS, True),
            create_field_filter("is_verified", FilterOperator.NOT_EQUALS, False),
            create_field_filter(
                "email",
                FilterOperator.IN,
                values=["a@example.com", "b@example.com"],
            ),
            create_field_filter("username", FilterOperator.NOT_IN, values=["bad"]),
            create_field_filter("deleted_at", FilterOperator.IS_NULL),
        ],
    )
    q = b.build_query(cfg)
    s = str(q)
    assert "WHERE" in s
    # Basic smoke that filters got included
    assert "is_superuser" in s and "is_verified" in s
