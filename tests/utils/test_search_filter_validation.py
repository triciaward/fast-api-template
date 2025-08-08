import pytest

pytestmark = pytest.mark.unit


def test_sort_validation_and_invalid_fields():
    from app.models import User
    from app.utils.search_filter import SearchFilterBuilder, SearchFilterConfig

    b = SearchFilterBuilder(User)
    # Invalid sort field ignored (no raise)
    cfg = SearchFilterConfig(sort_by="does_not_exist", sort_order="desc")
    q = b.build_query(cfg)
    assert "ORDER BY" not in str(q)

    # Valid sort field applied
    cfg2 = SearchFilterConfig(sort_by="email", sort_order="desc")
    q2 = b.build_query(cfg2)
    s = str(q2)
    assert "ORDER BY" in s and "email" in s


def test_text_search_fulltext_fallback_no_crash(monkeypatch):
    from app.models import User
    from app.utils.search_filter import (
        SearchFilterBuilder,
        SearchFilterConfig,
        create_text_search,
    )

    # Force use_full_text_search=True, but DB may not support tsquery in test env; code should fallback.
    ts = create_text_search("alpha", ["email", "username"], use_full_text_search=True)
    cfg = SearchFilterConfig(text_search=ts)
    b = SearchFilterBuilder(User)
    q = b.build_query(cfg)
    assert str(q)  # query built successfully



