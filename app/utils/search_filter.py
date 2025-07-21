from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Query


class SearchOperator(str, Enum):
    """Available search operators for text fields."""

    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"


class FilterOperator(str, Enum):
    """Available filter operators for comparison fields."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "gt"
    GREATER_THAN_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_EQUAL = "lte"
    IN = "in"
    NOT_IN = "not_in"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class TextSearchFilter(BaseModel):
    """Configuration for text search across multiple fields."""

    query: str = Field(..., description="Search query string")
    fields: list[str] = Field(..., description="Fields to search in")
    operator: SearchOperator = Field(
        default=SearchOperator.CONTAINS, description="Search operator to use"
    )
    case_sensitive: bool = Field(
        default=False, description="Whether search should be case sensitive"
    )
    use_full_text_search: bool = Field(
        default=False,
        description="Whether to use PostgreSQL full-text search (if available)",
    )


class FieldFilter(BaseModel):
    """Configuration for filtering a specific field."""

    field: str = Field(..., description="Field name to filter on")
    operator: FilterOperator = Field(..., description="Filter operator")
    value: Optional[Any] = Field(None, description="Value to filter by")
    values: Optional[list[Any]] = Field(
        None, description="List of values for IN/NOT_IN operators"
    )


class SearchFilterConfig(BaseModel):
    """Complete search and filter configuration."""

    text_search: Optional[TextSearchFilter] = Field(
        None, description="Text search configuration"
    )
    filters: list[FieldFilter] = Field(
        default_factory=list, description="List of field filters to apply"
    )
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: str = Field(default="asc", description="Sort order (asc or desc)")


class SearchFilterBuilder:
    """Builder class for constructing search and filter queries."""

    def __init__(self, model_class):
        self.model_class = model_class
        self._allowed_fields = self._get_model_fields()

    def _get_model_fields(self) -> list[str]:
        """Get list of allowed fields from the model."""
        return [column.name for column in self.model_class.__table__.columns]

    def _validate_field(self, field: str) -> bool:
        """Validate that a field exists in the model."""
        return field in self._allowed_fields

    def _validate_sort_field(self, field: str) -> bool:
        """Validate that a sort field exists in the model and is sortable."""
        if not self._validate_field(field):
            return False

        # Additional validation: ensure the field is not a complex type that can't be sorted
        # This is a basic check - you might want to add more specific validations
        column = getattr(self.model_class, field)
        return hasattr(column, "asc") and hasattr(column, "desc")

    def _build_text_search_condition(self, filter_config: TextSearchFilter) -> Any:
        """Build SQLAlchemy condition for text search."""
        if not filter_config.query.strip():
            return None

        search_conditions = []
        query = filter_config.query

        if not filter_config.case_sensitive:
            query = query.lower()

        # Use PostgreSQL full-text search if enabled and available
        if filter_config.use_full_text_search:
            try:
                # Create a full-text search condition using PostgreSQL's to_tsvector
                search_vector = func.to_tsvector(
                    "english",
                    " ".join(
                        [
                            func.coalesce(getattr(self.model_class, field), "")
                            for field in filter_config.fields
                        ]
                    ),
                )
                search_query = func.plainto_tsquery("english", query)
                return search_vector.op("@@")(search_query)
            except Exception:
                # Fall back to LIKE search if full-text search fails
                pass

        # Standard LIKE-based search
        for field_name in filter_config.fields:
            if not self._validate_field(field_name):
                continue

            field = getattr(self.model_class, field_name)

            if filter_config.operator == SearchOperator.CONTAINS:
                if not filter_config.case_sensitive:
                    condition = func.lower(field).contains(query)
                else:
                    condition = field.contains(query)
            elif filter_config.operator == SearchOperator.STARTS_WITH:
                if not filter_config.case_sensitive:
                    condition = func.lower(field).startswith(query)
                else:
                    condition = field.startswith(query)
            elif filter_config.operator == SearchOperator.ENDS_WITH:
                if not filter_config.case_sensitive:
                    condition = func.lower(field).endswith(query)
                else:
                    condition = field.endswith(query)
            elif filter_config.operator == SearchOperator.EQUALS:
                if not filter_config.case_sensitive:
                    condition = func.lower(field) == query
                else:
                    condition = field == query
            elif filter_config.operator == SearchOperator.NOT_EQUALS:
                if not filter_config.case_sensitive:
                    condition = func.lower(field) != query
                else:
                    condition = field != query
            else:
                continue

            search_conditions.append(condition)

        if not search_conditions:
            return None

        return or_(*search_conditions)

    def _build_field_filter_condition(self, filter_config: FieldFilter) -> Any:
        """Build SQLAlchemy condition for field filter."""
        if not self._validate_field(filter_config.field):
            return None

        field = getattr(self.model_class, filter_config.field)

        if filter_config.operator == FilterOperator.EQUALS:
            return field == filter_config.value
        elif filter_config.operator == FilterOperator.NOT_EQUALS:
            return field != filter_config.value
        elif filter_config.operator == FilterOperator.GREATER_THAN:
            return field > filter_config.value
        elif filter_config.operator == FilterOperator.GREATER_THAN_EQUAL:
            return field >= filter_config.value
        elif filter_config.operator == FilterOperator.LESS_THAN:
            return field < filter_config.value
        elif filter_config.operator == FilterOperator.LESS_THAN_EQUAL:
            return field <= filter_config.value
        elif filter_config.operator == FilterOperator.IN:
            if filter_config.values:
                return field.in_(filter_config.values)
        elif filter_config.operator == FilterOperator.NOT_IN:
            if filter_config.values:
                return ~field.in_(filter_config.values)
        elif filter_config.operator == FilterOperator.IS_NULL:
            return field.is_(None)
        elif filter_config.operator == FilterOperator.IS_NOT_NULL:
            return field.is_not(None)

        return None

    def build_query(self, config: SearchFilterConfig) -> Query:
        """Build a complete SQLAlchemy query with search and filters."""
        query = select(self.model_class)
        conditions = []

        # Add text search condition
        if config.text_search:
            text_condition = self._build_text_search_condition(config.text_search)
            if text_condition is not None:
                conditions.append(text_condition)

        # Add field filter conditions
        for field_filter in config.filters:
            filter_condition = self._build_field_filter_condition(field_filter)
            if filter_condition is not None:
                conditions.append(filter_condition)

        # Apply all conditions
        if conditions:
            query = query.filter(and_(*conditions))

        # Apply sorting
        if config.sort_by and self._validate_sort_field(config.sort_by):
            sort_field = getattr(self.model_class, config.sort_by)
            sort_order = config.sort_order.lower()
            if sort_order not in ["asc", "desc"]:
                sort_order = "asc"  # Default to ascending if invalid
            if sort_order == "desc":
                sort_field = sort_field.desc()
            query = query.order_by(sort_field)

        return query


# Convenience functions for common search patterns
def create_text_search(
    query: str,
    fields: list[str],
    operator: SearchOperator = SearchOperator.CONTAINS,
    case_sensitive: bool = False,
    use_full_text_search: bool = False,
) -> TextSearchFilter:
    """Create a text search filter configuration."""
    return TextSearchFilter(
        query=query,
        fields=fields,
        operator=operator,
        case_sensitive=case_sensitive,
        use_full_text_search=use_full_text_search,
    )


def create_field_filter(
    field: str,
    operator: FilterOperator,
    value: Optional[Any] = None,
    values: Optional[list[Any]] = None,
) -> FieldFilter:
    """Create a field filter configuration."""
    return FieldFilter(field=field, operator=operator, value=value, values=values)


# Pre-built filter configurations for common use cases
def create_user_search_filters(
    search_query: Optional[str] = None,
    use_full_text_search: bool = False,
    is_verified: Optional[bool] = None,
    oauth_provider: Optional[str] = None,
    is_superuser: Optional[bool] = None,
    is_deleted: Optional[bool] = None,
    date_created_after: Optional[datetime] = None,
    date_created_before: Optional[datetime] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
) -> SearchFilterConfig:
    """
    Create a search filter configuration for users.

    Args:
        search_query: Text to search in username and email fields
        use_full_text_search: Whether to use PostgreSQL full-text search
        is_verified: Filter by verification status
        oauth_provider: Filter by OAuth provider
        is_superuser: Filter by superuser status
        is_deleted: Filter by deletion status
        date_created_after: Filter users created after this date
        date_created_before: Filter users created before this date
        sort_by: Field to sort by
        sort_order: Sort order (asc or desc)

    Returns:
        SearchFilterConfig: Complete search and filter configuration
    """
    filters = []

    # Add text search if provided
    text_search = None
    if search_query:
        text_search = create_text_search(
            query=search_query,
            fields=["username", "email"],
            use_full_text_search=use_full_text_search,
        )

    # Add boolean filters
    if is_verified is not None:
        filters.append(
            create_field_filter("is_verified", FilterOperator.EQUALS, is_verified)
        )

    if is_superuser is not None:
        filters.append(
            create_field_filter("is_superuser", FilterOperator.EQUALS, is_superuser)
        )

    if is_deleted is not None:
        filters.append(
            create_field_filter("is_deleted", FilterOperator.EQUALS, is_deleted)
        )

    # Add OAuth provider filter
    if oauth_provider is not None:
        if oauth_provider == "none":
            filters.append(
                create_field_filter("oauth_provider", FilterOperator.IS_NULL)
            )
        else:
            filters.append(
                create_field_filter(
                    "oauth_provider", FilterOperator.EQUALS, oauth_provider
                )
            )

    # Add date range filters
    if date_created_after:
        filters.append(
            create_field_filter(
                "date_created", FilterOperator.GREATER_THAN_EQUAL, date_created_after
            )
        )

    if date_created_before:
        filters.append(
            create_field_filter(
                "date_created", FilterOperator.LESS_THAN_EQUAL, date_created_before
            )
        )

    return SearchFilterConfig(
        text_search=text_search, filters=filters, sort_by=sort_by, sort_order=sort_order
    )


# Query parameter models for FastAPI endpoints
class UserSearchParams(BaseModel):
    """Query parameters for user search endpoint."""

    search: Optional[str] = Field(
        None, description="Search query for username and email"
    )
    use_full_text_search: bool = Field(
        default=False, description="Use PostgreSQL full-text search (if available)"
    )
    is_verified: Optional[bool] = Field(
        None, description="Filter by verification status"
    )
    oauth_provider: Optional[str] = Field(
        None, description="Filter by OAuth provider (google, apple, none)"
    )
    is_superuser: Optional[bool] = Field(None, description="Filter by superuser status")
    is_deleted: Optional[bool] = Field(None, description="Filter by deletion status")
    date_created_after: Optional[datetime] = Field(
        None, description="Filter users created after this date"
    )
    date_created_before: Optional[datetime] = Field(
        None, description="Filter users created before this date"
    )
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: str = Field(default="asc", description="Sort order (asc or desc)")

    def to_search_config(self) -> SearchFilterConfig:
        """Convert search parameters to search configuration."""
        return create_user_search_filters(
            search_query=self.search,
            use_full_text_search=self.use_full_text_search,
            is_verified=self.is_verified,
            oauth_provider=self.oauth_provider,
            is_superuser=self.is_superuser,
            is_deleted=self.is_deleted,
            date_created_after=self.date_created_after,
            date_created_before=self.date_created_before,
            sort_by=self.sort_by,
            sort_order=self.sort_order,
        )
