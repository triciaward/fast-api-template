from app.models import User
from app.utils.search_filter import (
    FilterOperator,
    SearchFilterBuilder,
    SearchFilterConfig,
    create_field_filter,
    create_text_search,
)


def test_text_search_unknown_operator_with_valid_field_continues():
    ts = create_text_search("alpha", ["email"])  # defaults to contains
    # Force invalid operator to hit the fallback continue branch
    ts.operator = "unknown"  # type: ignore[attr-defined]
    cfg = SearchFilterConfig(text_search=ts)
    q = SearchFilterBuilder(User).build_query(cfg)
    # No WHERE since operator was unknown
    assert "WHERE" not in str(q)


def test_field_filter_is_not_null_branch():
    cfg = SearchFilterConfig(
        filters=[create_field_filter("oauth_provider", FilterOperator.IS_NOT_NULL)],
    )
    q = SearchFilterBuilder(User).build_query(cfg)
    s = str(q)
    assert "oauth_provider" in s


def test_field_filter_unknown_operator_falls_through():
    # Create a valid field filter then mutate operator to an unknown value
    ff = create_field_filter("email", FilterOperator.EQUALS, value="a@b.com")
    ff.operator = "unknown"  # type: ignore[attr-defined]
    cfg = SearchFilterConfig(filters=[ff])
    q = SearchFilterBuilder(User).build_query(cfg)
    # No WHERE since operator was unrecognized
    assert "WHERE" not in str(q)

