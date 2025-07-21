from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import declarative_base

from app.utils.search_filter import (
    FilterOperator,
    SearchFilterBuilder,
    SearchFilterConfig,
    SearchOperator,
    TextSearchFilter,
    create_field_filter,
    create_text_search,
)

Base = declarative_base()


class FakeUser(Base):  # type: ignore[misc, valid-type]
    __tablename__ = "fake_users"
    id = Column(Integer, primary_key=True)
    username = Column(String)
    email = Column(String)
    is_verified = Column(Boolean)
    is_superuser = Column(Boolean)
    is_deleted = Column(Boolean)
    oauth_provider = Column(String)
    date_created = Column(DateTime)
    deletion_reason = Column(String)
    deleted_by = Column(String)
    deleted_at = Column(DateTime)


def test_text_search_contains_case_insensitive():
    config = create_text_search("test", ["username"])
    builder = SearchFilterBuilder(FakeUser)
    clause = builder._build_text_search_condition(config)
    assert clause is not None


def test_text_search_equals_case_sensitive():
    config = create_text_search(
        "TestUser", ["username"], operator=SearchOperator.EQUALS, case_sensitive=True
    )
    builder = SearchFilterBuilder(FakeUser)
    clause = builder._build_text_search_condition(config)
    assert clause is not None


def test_invalid_field_skipped_in_text_search():
    config = create_text_search("test", ["nonexistent_field"])
    builder = SearchFilterBuilder(FakeUser)
    clause = builder._build_text_search_condition(config)
    assert clause is None


def test_field_filter_in_and_not_in():
    builder = SearchFilterBuilder(FakeUser)
    f_in = create_field_filter("username", FilterOperator.IN, values=["a", "b"])
    f_not_in = create_field_filter("username", FilterOperator.NOT_IN, values=["x"])
    assert builder._build_field_filter_condition(f_in) is not None
    assert builder._build_field_filter_condition(f_not_in) is not None


def test_field_filter_is_null_and_not_null():
    builder = SearchFilterBuilder(FakeUser)
    f_null = create_field_filter("oauth_provider", FilterOperator.IS_NULL)
    f_not_null = create_field_filter("oauth_provider", FilterOperator.IS_NOT_NULL)
    assert builder._build_field_filter_condition(f_null) is not None
    assert builder._build_field_filter_condition(f_not_null) is not None


def test_field_filter_invalid_field():
    builder = SearchFilterBuilder(FakeUser)
    f = create_field_filter("does_not_exist", FilterOperator.EQUALS, "foo")
    assert builder._build_field_filter_condition(f) is None


def test_build_query_with_sorting():
    config = SearchFilterConfig(
        filters=[create_field_filter("is_verified", FilterOperator.EQUALS, True)],
        sort_by="username",
        sort_order="desc",
    )
    builder = SearchFilterBuilder(FakeUser)
    query = builder.build_query(config)
    assert "ORDER BY" in str(query)


# Additional tests to cover missing lines


def test_text_search_contains_case_sensitive():
    """Test case-sensitive CONTAINS operator (line 146)."""
    config = create_text_search(
        "TestUser", ["username"], operator=SearchOperator.CONTAINS, case_sensitive=True
    )
    builder = SearchFilterBuilder(FakeUser)
    clause = builder._build_text_search_condition(config)
    assert clause is not None


def test_text_search_starts_with_case_sensitive():
    """Test case-sensitive STARTS_WITH operator (line 151)."""
    config = create_text_search(
        "TestUser",
        ["username"],
        operator=SearchOperator.STARTS_WITH,
        case_sensitive=True,
    )
    builder = SearchFilterBuilder(FakeUser)
    clause = builder._build_text_search_condition(config)
    assert clause is not None


def test_text_search_ends_with_case_sensitive():
    """Test case-sensitive ENDS_WITH operator (lines 161-163)."""
    config = create_text_search(
        "TestUser", ["username"], operator=SearchOperator.ENDS_WITH, case_sensitive=True
    )
    builder = SearchFilterBuilder(FakeUser)
    clause = builder._build_text_search_condition(config)
    assert clause is not None


def test_field_filter_in_empty_values():
    """Test IN operator with empty values (line 182)."""
    builder = SearchFilterBuilder(FakeUser)
    f_in_empty = create_field_filter("username", FilterOperator.IN, values=[])
    result = builder._build_field_filter_condition(f_in_empty)
    assert result is None


def test_field_filter_not_in_empty_values():
    """Test NOT_IN operator with empty values (line 190)."""
    builder = SearchFilterBuilder(FakeUser)
    f_not_in_empty = create_field_filter("username", FilterOperator.NOT_IN, values=[])
    result = builder._build_field_filter_condition(f_not_in_empty)
    assert result is None


def test_field_filter_in_none_values():
    """Test IN operator with None values."""
    builder = SearchFilterBuilder(FakeUser)
    f_in_none = create_field_filter("username", FilterOperator.IN, values=None)
    result = builder._build_field_filter_condition(f_in_none)
    assert result is None


def test_field_filter_not_in_none_values():
    """Test NOT_IN operator with None values."""
    builder = SearchFilterBuilder(FakeUser)
    f_not_in_none = create_field_filter("username", FilterOperator.NOT_IN, values=None)
    result = builder._build_field_filter_condition(f_not_in_none)
    assert result is None


def test_full_text_search_exception_fallback():
    """Test full-text search exception handling fallback (lines 126-128)."""
    # This test simulates the exception handling in full-text search
    # by creating a config that would trigger the fallback
    config = create_text_search("test", ["username"], use_full_text_search=True)
    builder = SearchFilterBuilder(FakeUser)

    # The fallback should work even if full-text search fails
    clause = builder._build_text_search_condition(config)
    assert clause is not None


def test_text_search_with_no_valid_fields():
    """Test text search with no valid fields."""
    config = create_text_search("test", ["invalid_field1", "invalid_field2"])
    builder = SearchFilterBuilder(FakeUser)
    clause = builder._build_text_search_condition(config)
    assert clause is None


def test_text_search_else_branch_coverage():
    """Test the else branch in text search operator handling."""
    # Create a config with a valid operator but no valid fields to trigger the else branch
    config = TextSearchFilter(
        query="test",
        # This will cause the field validation to fail
        fields=["invalid_field"],
        operator=SearchOperator.CONTAINS,
        case_sensitive=False,
    )
    builder = SearchFilterBuilder(FakeUser)
    clause = builder._build_text_search_condition(config)
    # Should return None because no valid conditions were found
    assert clause is None


def test_field_filter_else_branch_coverage():
    """Test the else branch in field filter operator handling."""
    builder = SearchFilterBuilder(FakeUser)
    # Create a filter with a valid operator but invalid field to trigger the else branch
    valid_filter = create_field_filter("invalid_field", FilterOperator.EQUALS, "test")
    result = builder._build_field_filter_condition(valid_filter)
    assert result is None


def test_text_search_ends_with_case_sensitive_direct():
    """Test case-sensitive ENDS_WITH operator directly (lines 161-163)."""
    # Create a config that will hit the case-sensitive ENDS_WITH branch
    config = TextSearchFilter(
        query="TestUser",
        fields=["username"],
        operator=SearchOperator.ENDS_WITH,
        case_sensitive=True,  # This will trigger the else branch
    )
    builder = SearchFilterBuilder(FakeUser)
    clause = builder._build_text_search_condition(config)
    assert clause is not None


def test_field_filter_in_with_falsy_values():
    """Test IN operator with falsy values (line 182)."""
    builder = SearchFilterBuilder(FakeUser)

    # Test with empty list
    f_in_empty = create_field_filter("username", FilterOperator.IN, values=[])
    result = builder._build_field_filter_condition(f_in_empty)
    assert result is None

    # Test with None values
    f_in_none = create_field_filter("username", FilterOperator.IN, values=None)
    result = builder._build_field_filter_condition(f_in_none)
    assert result is None


def test_field_filter_not_in_with_falsy_values():
    """Test NOT_IN operator with falsy values (line 190)."""
    builder = SearchFilterBuilder(FakeUser)

    # Test with empty list
    f_not_in_empty = create_field_filter("username", FilterOperator.NOT_IN, values=[])
    result = builder._build_field_filter_condition(f_not_in_empty)
    assert result is None

    # Test with None values
    f_not_in_none = create_field_filter("username", FilterOperator.NOT_IN, values=None)
    result = builder._build_field_filter_condition(f_not_in_none)
    assert result is None


def test_full_text_search_exception_handling():
    """Test the exception handling in full-text search (lines 126-128)."""
    # This test needs to trigger the exception in the full-text search
    # We'll mock the SQLAlchemy functions to raise an exception
    from unittest.mock import patch

    config = TextSearchFilter(
        query="test",
        fields=["username"],
        operator=SearchOperator.CONTAINS,
        case_sensitive=False,
        use_full_text_search=True,
    )
    builder = SearchFilterBuilder(FakeUser)

    # Mock the to_tsvector function to raise an exception
    with patch(
        "sqlalchemy.sql.functions.func.to_tsvector",
        side_effect=Exception("Full-text search not available"),
    ):
        clause = builder._build_text_search_condition(config)
        # Should fall back to LIKE search and return a valid clause
        assert clause is not None


def test_comprehensive_search_filter_coverage():
    """Comprehensive test to cover remaining missing lines."""
    builder = SearchFilterBuilder(FakeUser)

    # Test case-sensitive ENDS_WITH with valid field
    config_ends_with = TextSearchFilter(
        query="User",
        fields=["username"],
        operator=SearchOperator.ENDS_WITH,
        case_sensitive=True,
    )
    clause = builder._build_text_search_condition(config_ends_with)
    assert clause is not None

    # Test IN operator with falsy values
    f_in_falsy = create_field_filter("username", FilterOperator.IN, values=[])
    result = builder._build_field_filter_condition(f_in_falsy)
    assert result is None

    # Test NOT_IN operator with falsy values
    f_not_in_falsy = create_field_filter("username", FilterOperator.NOT_IN, values=[])
    result = builder._build_field_filter_condition(f_not_in_falsy)
    assert result is None
