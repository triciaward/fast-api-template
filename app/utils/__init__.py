"""
Utility modules for the FastAPI application.

This package contains utility modules that provide common functionality
across the application.
"""

from .datetime_utils import (
    format_datetime,
    is_expired,
    is_near_expiry,
    parse_datetime,
    time_until,
    utc_now,
)
from .pagination import (
    PaginatedResponse,
    PaginatedResponseWithLinks,
    PaginationMetadata,
    PaginationParams,
    create_pagination_links,
    paginate,
)

__all__ = [
    # Datetime utilities
    "utc_now",
    "format_datetime",
    "parse_datetime",
    "is_expired",
    "time_until",
    "is_near_expiry",
    # Pagination utilities
    "PaginatedResponse",
    "PaginatedResponseWithLinks",
    "PaginationMetadata",
    "PaginationParams",
    "create_pagination_links",
    "paginate",
]
