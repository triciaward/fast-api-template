from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.orm import declarative_base

if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase

    Base = DeclarativeBase
else:
    Base = declarative_base()


class Dummy(Base):
    __tablename__ = "dummy"
    id = Column(String, primary_key=True)
    username = Column(String)
    email = Column(String)
    is_verified = Column(Boolean)
    is_superuser = Column(Boolean)
    is_deleted = Column(Boolean)
    date_created = Column(DateTime(timezone=True))
    deleted_at = Column(DateTime(timezone=True))
    deletion_reason = Column(String)


def test_text_search_contains_case_insensitive():
    from app.utils.search_filter import (
        SearchFilterBuilder,
        SearchFilterConfig,
        create_text_search,
    )

    builder = SearchFilterBuilder(Dummy)
    config = SearchFilterConfig(
        text_search=create_text_search("Alice", ["username", "email"]),
    )
    query = builder.build_query(config)
    sql = str(query)
    assert "lower(dummy.username)" in sql or "lower(dummy.email)" in sql


def test_field_filters_and_sorting():
    from app.utils.search_filter import (
        FilterOperator,
        SearchFilterBuilder,
        SearchFilterConfig,
        create_field_filter,
    )

    builder = SearchFilterBuilder(Dummy)
    filters = [
        create_field_filter("is_verified", FilterOperator.EQUALS, True),
        create_field_filter("is_deleted", FilterOperator.EQUALS, False),
        create_field_filter(
            "date_created",
            FilterOperator.GREATER_THAN_EQUAL,
            datetime(2025, 1, 1, tzinfo=timezone.utc),
        ),
    ]
    config = SearchFilterConfig(filters=filters, sort_by="username", sort_order="desc")
    query = builder.build_query(config)
    sql = str(query)
    assert "dummy.is_verified" in sql and "dummy.is_deleted" in sql
    assert "ORDER BY" in sql and "DESC" in sql.upper()


def test_in_not_in_and_null_filters():
    from app.utils.search_filter import (
        FilterOperator,
        SearchFilterBuilder,
        SearchFilterConfig,
        create_field_filter,
    )

    builder = SearchFilterBuilder(Dummy)
    filters = [
        create_field_filter("username", FilterOperator.IN, values=["a", "b"]),
        create_field_filter("email", FilterOperator.NOT_IN, values=["x@example.com"]),
        create_field_filter("deleted_at", FilterOperator.IS_NULL),
    ]
    config = SearchFilterConfig(filters=filters)
    query = builder.build_query(config)
    sql = str(query)
    assert "IN" in sql.upper()
    assert "NOT" in sql.upper() and "IN" in sql.upper()
    assert "deleted_at" in sql


import pytest

pytestmark = pytest.mark.template_only


def test_stub_search_filter() -> None:
    assert True
