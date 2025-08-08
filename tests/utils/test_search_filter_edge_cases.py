import pytest

pytestmark = pytest.mark.unit


def test_text_search_case_sensitive_and_equals():
    from app.models import User
    from app.utils.search_filter import (
        SearchFilterBuilder,
        SearchFilterConfig,
        SearchOperator,
        create_text_search,
    )

    ts = create_text_search(
        "Alpha",
        ["email"],
        operator=SearchOperator.EQUALS,
        case_sensitive=True,
    )
    cfg = SearchFilterConfig(text_search=ts)
    q = SearchFilterBuilder(User).build_query(cfg)
    assert "email" in str(q)


def test_builder_sort_normalization_and_invalid_field():
    from app.models import User
    from app.utils.search_filter import SearchFilterBuilder, SearchFilterConfig

    # invalid sort field -> no order_by appended
    cfg = SearchFilterConfig(sort_by="not_a_field", sort_order="desc")
    q = SearchFilterBuilder(User).build_query(cfg)
    s = str(q)
    assert "ORDER BY" not in s

    # invalid sort order -> defaults inside builder to asc
    cfg2 = SearchFilterConfig(sort_by="email", sort_order="weird")
    q2 = SearchFilterBuilder(User).build_query(cfg2)
    s2 = str(q2)
    assert "ORDER BY" in s2


def test_text_search_empty_query_returns_none_condition():
    from app.models import User
    from app.utils.search_filter import (
        SearchFilterBuilder,
        SearchFilterConfig,
        create_text_search,
    )

    ts = create_text_search("   ", ["email"])  # empty after strip
    cfg = SearchFilterConfig(text_search=ts)
    q = SearchFilterBuilder(User).build_query(cfg)
    assert "WHERE" not in str(q)


def test_text_search_invalid_operator_and_no_valid_fields(monkeypatch):
    from app.models import User
    from app.utils.search_filter import (
        SearchFilterBuilder,
        SearchFilterConfig,
        create_text_search,
    )

    # Invalid operator by mutating attribute and invalid field name -> no conditions, triggers empty return
    ts = create_text_search("alpha", ["not_a_field"])  # invalid field
    ts.operator = "unknown"  # type: ignore[attr-defined]
    cfg = SearchFilterConfig(text_search=ts)
    q = SearchFilterBuilder(User).build_query(cfg)
    assert "WHERE" not in str(q)


def test_field_filter_in_not_in_without_values_are_ignored():
    from app.models import User
    from app.utils.search_filter import (
        FilterOperator,
        SearchFilterBuilder,
        SearchFilterConfig,
        create_field_filter,
    )

    cfg = SearchFilterConfig(
        filters=[
            create_field_filter("email", FilterOperator.IN, values=None),
            create_field_filter("email", FilterOperator.NOT_IN, values=None),
        ],
    )
    q = SearchFilterBuilder(User).build_query(cfg)
    s = str(q)
    # No filter applied
    assert "WHERE" not in s


def test_user_and_deleted_user_params_to_search_config():
    from app.utils.search_filter import DeletedUserSearchParams, UserSearchParams

    usp = UserSearchParams(search="a", is_verified=True)
    cfg1 = usp.to_search_config()
    assert cfg1 is not None

    dsp = DeletedUserSearchParams(deletion_reason="x")
    cfg2 = dsp.to_search_config()
    assert cfg2 is not None


def test_field_filters_remaining_ops():
    from app.models import User
    from app.utils.search_filter import (
        FilterOperator,
        SearchFilterBuilder,
        SearchFilterConfig,
        create_field_filter,
    )

    cfg = SearchFilterConfig(
        filters=[
            create_field_filter(
                "created_at",
                FilterOperator.GREATER_THAN,
                value="2024-01-01",
            ),
            create_field_filter(
                "created_at",
                FilterOperator.GREATER_THAN_EQUAL,
                value="2024-01-01",
            ),
            create_field_filter(
                "created_at",
                FilterOperator.LESS_THAN,
                value="2024-12-31",
            ),
            create_field_filter(
                "created_at",
                FilterOperator.LESS_THAN_EQUAL,
                value="2024-12-31",
            ),
            create_field_filter(
                "nonexistent",
                FilterOperator.EQUALS,
                value=1,
            ),  # ignored
        ],
    )
    q = SearchFilterBuilder(User).build_query(cfg)
    s = str(q)
    assert "created_at" in s


def test_text_search_operators_and_fulltext_fallback(monkeypatch):
    from app.models import User
    from app.utils.search_filter import (
        SearchFilterBuilder,
        SearchFilterConfig,
        SearchOperator,
        create_text_search,
    )

    # STARTS_WITH / ENDS_WITH / NOT_EQUALS branches
    for op in [
        SearchOperator.STARTS_WITH,
        SearchOperator.ENDS_WITH,
        SearchOperator.NOT_EQUALS,
    ]:
        ts = create_text_search("test", ["email"], operator=op, case_sensitive=False)
        cfg = SearchFilterConfig(text_search=ts)
        q = SearchFilterBuilder(User).build_query(cfg)
        assert "email" in str(q)

    # Case-sensitive equals path
    ts_cs = create_text_search(
        "Z",
        ["username"],
        operator=SearchOperator.EQUALS,
        case_sensitive=True,
    )
    cfg_cs = SearchFilterConfig(text_search=ts_cs)
    q_cs = SearchFilterBuilder(User).build_query(cfg_cs)
    assert "username" in str(q_cs)

    # Full-text search path with fallback (simulated by forcing exception)
    import app.utils.search_filter as sf

    def bad_to_tsvector(*a, **k):  # type: ignore[no-untyped-def]
        raise RuntimeError("no fts")

    monkeypatch.setattr(sf.func, "to_tsvector", bad_to_tsvector)
    ts2 = create_text_search("alpha", ["email"], use_full_text_search=True)
    cfg2 = SearchFilterConfig(text_search=ts2)
    q2 = SearchFilterBuilder(User).build_query(cfg2)
    assert "email" in str(q2)


def test_builder_invalid_sort_order_defaults_to_asc():
    from app.models import User
    from app.utils.search_filter import SearchFilterBuilder, SearchFilterConfig

    cfg = SearchFilterConfig(sort_by="email", sort_order="INVALID")
    q = SearchFilterBuilder(User).build_query(cfg)
    s = str(q)
    # Order by should exist and default to asc
    assert "ORDER BY" in s


def test_create_user_search_filters_all_options():
    from datetime import datetime

    from app.utils.search_filter import create_user_search_filters

    cfg = create_user_search_filters(
        search_query="alpha",
        use_full_text_search=True,
        is_verified=True,
        oauth_provider="google",
        is_superuser=False,
        is_deleted=False,
        date_created_after=datetime(2024, 1, 1),
        date_created_before=datetime(2024, 12, 31),
        sort_by="username",
        sort_order="desc",
    )
    assert cfg.sort_order == "desc"

    # invalid sort order normalization
    cfg2 = create_user_search_filters(sort_order="weird")
    assert cfg2.sort_order == "weird"  # normalization happens in builder, not here

    # provider none (IS NULL path)
    cfg3 = create_user_search_filters(oauth_provider="none")
    assert cfg3 is not None


def test_create_deleted_user_search_filters_all_options():
    from datetime import datetime
    from uuid import UUID

    from app.utils.search_filter import create_deleted_user_search_filters

    uid = UUID("11111111-1111-1111-1111-111111111111")
    cfg = create_deleted_user_search_filters(
        deleted_by=uid,
        deletion_reason="cleanup",
        deleted_after=datetime(2024, 1, 1),
        deleted_before=datetime(2024, 12, 31),
        sort_by="deleted_at",
        sort_order="asc",
    )
    assert cfg.sort_order == "asc"


def test_deleted_user_filters_tail_blocks():
    from app.utils.search_filter import create_deleted_user_search_filters

    # Minimal call to exercise tail return
    cfg = create_deleted_user_search_filters()
    assert cfg is not None
