"""
Pagination utilities for FastAPI applications.

This module provides generic pagination helpers and response schemas for consistent
pagination across all API endpoints.
"""

import math
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters for pagination."""

    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    size: int = Field(default=20, ge=1, le=100, description="Number of items per page")

    @property
    def skip(self) -> int:
        """Calculate the number of items to skip."""
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        """Get the limit (same as size for consistency)."""
        return self.size


class PaginationMetadata(BaseModel):
    """Metadata for paginated responses."""

    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page")
    total: int = Field(..., description="Total number of items")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")
    next_page: int | None = Field(None, description="Next page number")
    prev_page: int | None = Field(None, description="Previous page number")

    @classmethod
    def create(cls, page: int, size: int, total: int) -> "PaginationMetadata":
        """Create pagination metadata from basic parameters."""
        pages = math.ceil(total / size) if total > 0 else 0
        has_next = page < pages
        has_prev = page > 1
        next_page = page + 1 if has_next else None
        prev_page = page - 1 if has_prev else None

        return cls(
            page=page,
            size=size,
            total=total,
            pages=pages,
            has_next=has_next,
            has_prev=has_prev,
            next_page=next_page,
            prev_page=prev_page,
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response schema."""

    items: list[T] = Field(..., description="List of items")
    metadata: PaginationMetadata = Field(..., description="Pagination metadata")

    @classmethod
    def create(
        cls,
        items: list[T],
        page: int,
        size: int,
        total: int,
    ) -> "PaginatedResponse[T]":
        """Create a paginated response from items and pagination parameters."""
        metadata = PaginationMetadata.create(page=page, size=size, total=total)
        return cls(items=items, metadata=metadata)


async def paginate(
    query: Any,
    page: int = 1,
    size: int = 20,
    max_size: int = 100,
) -> PaginatedResponse[Any]:
    """
    Generic pagination helper for async SQLAlchemy queries.

    Args:
        query: Async SQLAlchemy query object
        page: Page number (1-based)
        size: Number of items per page
        max_size: Maximum allowed page size

    Returns:
        PaginatedResponse with items and metadata
    """
    # Validate and clamp size
    size = min(size, max_size)
    size = max(1, size)

    # Calculate skip
    skip = (page - 1) * size

    # Get total count
    total = await query.count()

    # Get paginated results
    items = await query.offset(skip).limit(size).all()

    # Create metadata
    metadata = PaginationMetadata.create(page=page, size=size, total=total)

    return PaginatedResponse(items=items, metadata=metadata)


def create_pagination_links(
    base_url: str,
    page: int,
    pages: int,
    **query_params: Any,
) -> dict[str, str | None]:
    """
    Create pagination links for HATEOAS support.

    Args:
        base_url: Base URL for the endpoint
        page: Current page number
        pages: Total number of pages
        **query_params: Additional query parameters to include

    Returns:
        Dictionary with pagination links
    """
    links: dict[str, str | None] = {}

    # Build query string
    query_parts = []
    for key, value in query_params.items():
        if value is not None:
            query_parts.append(f"{key}={value}")

    query_string = "&".join(query_parts)
    separator = "&" if query_string else ""

    # First page
    links["first"] = f"{base_url}?page=1{separator}{query_string}"

    # Previous page
    if page > 1:
        links["prev"] = f"{base_url}?page={page-1}{separator}{query_string}"
    else:
        links["prev"] = None

    # Current page
    links["self"] = f"{base_url}?page={page}{separator}{query_string}"

    # Next page
    if page < pages:
        links["next"] = f"{base_url}?page={page+1}{separator}{query_string}"
    else:
        links["next"] = None

    # Last page
    links["last"] = f"{base_url}?page={pages}{separator}{query_string}"

    return links


class PaginatedResponseWithLinks(PaginatedResponse[T]):
    """Paginated response with HATEOAS links."""

    links: dict[str, str | None] = Field(..., description="Pagination links")

    @classmethod
    def create_with_links(
        cls,
        items: list[T],
        page: int,
        size: int,
        total: int,
        base_url: str,
        **query_params: Any,
    ) -> "PaginatedResponseWithLinks[T]":
        """Create a paginated response with HATEOAS links."""
        metadata = PaginationMetadata.create(page=page, size=size, total=total)
        links = create_pagination_links(
            base_url=base_url,
            page=page,
            pages=metadata.pages,
            size=size,
            **query_params,
        )

        return cls(items=items, metadata=metadata, links=links)
