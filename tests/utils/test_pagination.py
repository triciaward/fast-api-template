from app.utils.pagination import (
    PaginatedResponseWithLinks,
    PaginationMetadata,
    create_pagination_links,
)


def test_pagination_metadata_basic():
    meta = PaginationMetadata.create(page=2, size=10, total=35)
    assert meta.pages == 4
    assert meta.has_next is True and meta.next_page == 3
    assert meta.has_prev is True and meta.prev_page == 1


def test_create_pagination_links():
    links = create_pagination_links("/items", page=2, pages=5, q="abc")
    assert links["self"].startswith("/items?page=2")
    assert links["prev"].startswith("/items?page=1")
    assert links["next"].startswith("/items?page=3")
    assert links["last"].endswith("page=5&q=abc")


def test_paginated_response_with_links():
    resp = PaginatedResponseWithLinks.create_with_links(
        items=[1, 2, 3], page=1, size=3, total=9, base_url="/x", q=None,
    )
    assert resp.metadata.pages == 3
    assert resp.links["first"].startswith("/x?page=1")
import pytest

from app.utils.pagination import PaginatedResponse

pytestmark = pytest.mark.template_only


def test_paginated_response_type_parametric() -> None:
    assert hasattr(PaginatedResponse, "__class_getitem__")


def test_pagination_metadata_edges():
    """Test pagination metadata edge cases."""
    from app.utils.pagination import PaginationMetadata

    m0 = PaginationMetadata.create(page=1, size=20, total=0)
    assert m0.pages == 0 and m0.has_next is False and m0.has_prev is False
    assert m0.next_page is None and m0.prev_page is None

    m1 = PaginationMetadata.create(page=1, size=10, total=9)
    assert m1.pages == 1 and m1.has_next is False and m1.has_prev is False

    m2 = PaginationMetadata.create(page=2, size=10, total=25)
    assert m2.pages == 3 and m2.has_next is True and m2.next_page == 3 and m2.prev_page == 1


def test_create_pagination_links_variants():
    """Test pagination links with various parameters."""
    from app.utils.pagination import create_pagination_links

    links = create_pagination_links("/api/items", page=1, pages=3, q="x", sort="name")
    assert links["first"].startswith("/api/items?page=1")
    assert links["prev"] is None
    assert links["self"].startswith("/api/items?page=1")
    assert links["next"].startswith("/api/items?page=2")
    assert links["last"].startswith("/api/items?page=3")
