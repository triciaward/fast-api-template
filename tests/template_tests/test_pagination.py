"""
Tests for pagination utilities.

This module tests the pagination helper functions and response schemas.
"""

from app.utils.pagination import (
    PaginatedResponse,
    PaginationMetadata,
    PaginationParams,
    create_pagination_links,
)


class TestPaginationParams:
    """Test PaginationParams class."""

    def test_default_values(self):
        """Test default pagination parameters."""
        params = PaginationParams()
        assert params.page == 1
        assert params.size == 20
        assert params.skip == 0
        assert params.limit == 20

    def test_custom_values(self):
        """Test custom pagination parameters."""
        params = PaginationParams(page=3, size=50)
        assert params.page == 3
        assert params.size == 50
        assert params.skip == 100  # (3-1) * 50
        assert params.limit == 50

    def test_skip_calculation(self):
        """Test skip calculation for different pages."""
        params = PaginationParams(page=1, size=10)
        assert params.skip == 0

        params = PaginationParams(page=2, size=10)
        assert params.skip == 10

        params = PaginationParams(page=5, size=25)
        assert params.skip == 100


class TestPaginationMetadata:
    """Test PaginationMetadata class."""

    def test_create_metadata(self):
        """Test metadata creation."""
        metadata = PaginationMetadata.create(page=1, size=20, total=100)

        assert metadata.page == 1
        assert metadata.size == 20
        assert metadata.total == 100
        assert metadata.pages == 5
        assert metadata.has_next is True
        assert metadata.has_prev is False
        assert metadata.next_page == 2
        assert metadata.prev_page is None

    def test_last_page_metadata(self):
        """Test metadata for last page."""
        metadata = PaginationMetadata.create(page=5, size=20, total=100)

        assert metadata.page == 5
        assert metadata.pages == 5
        assert metadata.has_next is False
        assert metadata.has_prev is True
        assert metadata.next_page is None
        assert metadata.prev_page == 4

    def test_middle_page_metadata(self):
        """Test metadata for middle page."""
        metadata = PaginationMetadata.create(page=3, size=20, total=100)

        assert metadata.page == 3
        assert metadata.pages == 5
        assert metadata.has_next is True
        assert metadata.has_prev is True
        assert metadata.next_page == 4
        assert metadata.prev_page == 2

    def test_empty_results(self):
        """Test metadata for empty results."""
        metadata = PaginationMetadata.create(page=1, size=20, total=0)

        assert metadata.page == 1
        assert metadata.total == 0
        assert metadata.pages == 0
        assert metadata.has_next is False
        assert metadata.has_prev is False
        assert metadata.next_page is None
        assert metadata.prev_page is None

    def test_partial_last_page(self):
        """Test metadata for partial last page."""
        metadata = PaginationMetadata.create(page=3, size=20, total=55)

        assert metadata.page == 3
        assert metadata.total == 55
        assert metadata.pages == 3
        assert metadata.has_next is False
        assert metadata.has_prev is True


class TestPaginatedResponse:
    """Test PaginatedResponse class."""

    def test_create_response(self):
        """Test creating a paginated response."""
        items = ["item1", "item2", "item3"]
        response = PaginatedResponse.create(items=items, page=1, size=20, total=100)

        assert response.items == items
        assert response.metadata.page == 1
        assert response.metadata.size == 20
        assert response.metadata.total == 100
        assert response.metadata.pages == 5

    def test_response_with_empty_items(self) -> None:
        """Test response with empty items list."""
        response: PaginatedResponse[list] = PaginatedResponse.create(
            items=[],
            page=1,
            size=20,
            total=0,
        )

        assert response.items == []
        assert response.metadata.total == 0
        assert response.metadata.pages == 0


class TestPaginationLinks:
    """Test pagination links creation."""

    def test_create_basic_links(self):
        """Test creating basic pagination links."""
        links = create_pagination_links(base_url="/api/users", page=1, pages=5, size=20)

        assert links["first"] == "/api/users?page=1&size=20"
        assert links["self"] == "/api/users?page=1&size=20"
        assert links["next"] == "/api/users?page=2&size=20"
        assert links["last"] == "/api/users?page=5&size=20"
        assert links["prev"] is None

    def test_create_links_with_additional_params(self):
        """Test creating links with additional query parameters."""
        links = create_pagination_links(
            base_url="/api/users",
            page=3,
            pages=5,
            size=20,
            is_verified=True,
            oauth_provider="google",
        )

        assert (
            links["first"]
            == "/api/users?page=1&size=20&is_verified=True&oauth_provider=google"
        )
        assert (
            links["self"]
            == "/api/users?page=3&size=20&is_verified=True&oauth_provider=google"
        )
        assert (
            links["next"]
            == "/api/users?page=4&size=20&is_verified=True&oauth_provider=google"
        )
        assert (
            links["prev"]
            == "/api/users?page=2&size=20&is_verified=True&oauth_provider=google"
        )
        assert (
            links["last"]
            == "/api/users?page=5&size=20&is_verified=True&oauth_provider=google"
        )

    def test_create_links_last_page(self):
        """Test creating links for last page."""
        links = create_pagination_links(base_url="/api/users", page=5, pages=5, size=20)

        assert links["first"] == "/api/users?page=1&size=20"
        assert links["self"] == "/api/users?page=5&size=20"
        assert links["next"] is None
        assert links["prev"] == "/api/users?page=4&size=20"
        assert links["last"] == "/api/users?page=5&size=20"

    def test_create_links_single_page(self):
        """Test creating links for single page results."""
        links = create_pagination_links(base_url="/api/users", page=1, pages=1, size=20)

        assert links["first"] == "/api/users?page=1&size=20"
        assert links["self"] == "/api/users?page=1&size=20"
        assert links["next"] is None
        assert links["prev"] is None
        assert links["last"] == "/api/users?page=1&size=20"


class TestPaginationIntegration:
    """Test pagination integration scenarios."""

    def test_full_pagination_flow(self):
        """Test complete pagination flow."""
        # Create pagination params
        params = PaginationParams(page=2, size=10)

        # Mock items
        items = [f"item_{i}" for i in range(10)]
        total = 25

        # Create response
        response = PaginatedResponse.create(
            items=items,
            page=params.page,
            size=params.size,
            total=total,
        )

        # Verify response structure
        assert response.items == items
        assert response.metadata.page == 2
        assert response.metadata.size == 10
        assert response.metadata.total == 25
        assert response.metadata.pages == 3
        assert response.metadata.has_next is True
        assert response.metadata.has_prev is True
        assert response.metadata.next_page == 3
        assert response.metadata.prev_page == 1

    def test_pagination_with_filters(self):
        """Test pagination with filter parameters."""
        # Create links with filters
        links = create_pagination_links(
            base_url="/api/users",
            page=1,
            pages=3,
            size=20,
            is_verified=True,
            oauth_provider="google",
            search="test",
        )

        # Verify all parameters are included
        expected_params = (
            "page=1&size=20&is_verified=True&oauth_provider=google&search=test"
        )
        assert links["self"] == f"/api/users?{expected_params}"
