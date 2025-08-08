from app.models import User
from app.utils.search_filter import (
    FilterOperator,
    SearchFilterBuilder,
    SearchFilterConfig,
    SearchOperator,
    create_field_filter,
    create_text_search,
)


def test_text_search_case_sensitive_variants():
    # CONTAINS, STARTS_WITH, ENDS_WITH with case_sensitive=True
    for op in [
        SearchOperator.CONTAINS,
        SearchOperator.STARTS_WITH,
        SearchOperator.ENDS_WITH,
    ]:
        ts = create_text_search("Alpha", ["email"], operator=op, case_sensitive=True)
        cfg = SearchFilterConfig(text_search=ts)
        q = SearchFilterBuilder(User).build_query(cfg)
        assert "email" in str(q)


def test_text_search_equals_insensitive_and_not_equals_sensitive():
    # equals, case-insensitive path
    ts_eq = create_text_search(
        "alpha", ["username"], operator=SearchOperator.EQUALS, case_sensitive=False,
    )
    cfg_eq = SearchFilterConfig(text_search=ts_eq)
    q_eq = SearchFilterBuilder(User).build_query(cfg_eq)
    assert "username" in str(q_eq)

    # not_equals, case-sensitive path
    ts_ne = create_text_search(
        "alpha", ["username"], operator=SearchOperator.NOT_EQUALS, case_sensitive=True,
    )
    cfg_ne = SearchFilterConfig(text_search=ts_ne)
    q_ne = SearchFilterBuilder(User).build_query(cfg_ne)
    assert "username" in str(q_ne)


def test_field_filter_not_in_and_in_with_values():
    cfg = SearchFilterConfig(
        filters=[
            create_field_filter(
                "email", FilterOperator.IN, values=["a@b.com", "c@d.com"],
            ),
            create_field_filter("email", FilterOperator.NOT_IN, values=["x@y.com"]),
        ],
    )
    q = SearchFilterBuilder(User).build_query(cfg)
    s = str(q)
    assert "email" in s and "SELECT" in s
