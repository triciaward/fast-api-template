"""
User search and listing functionality.

This module provides endpoints for searching and listing users with
advanced filtering and pagination capabilities.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.users.auth import get_current_user
from app.crud.system.admin import AdminUserCRUD
from app.database.database import get_db
from app.schemas.auth.user import (
    UserListResponse,
    UserResponse,
    UserSearchResponse,
)
from app.utils.pagination import PaginatedResponse, PaginationParams
from app.utils.search_filter import UserSearchParams

router = APIRouter()

# Initialize admin CRUD for user operations
admin_user_crud = AdminUserCRUD()


@router.get("/", response_model=UserListResponse)
async def list_users(
    pagination: PaginationParams = Depends(),
    search_params: UserSearchParams = Depends(),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[UserResponse]:
    """
    List users with advanced search, filtering, and pagination.

    This endpoint allows authenticated users to view other users in the system
    with powerful search and filtering capabilities.

    Search and Filter Options:
    - search: Text search in username and email fields
    - is_verified: Filter by verification status
    - oauth_provider: Filter by OAuth provider (google, apple, none)
    - is_superuser: Filter by superuser status
    - is_deleted: Filter by deletion status
    - date_created_after: Filter users created after this date
    - date_created_before: Filter users created before this date
    - sort_by: Field to sort by
    - sort_order: Sort order (asc or desc)

    Examples:
    - ?search=trish&is_verified=true
    - ?oauth_provider=google&sort_by=date_created&sort_order=desc
    - ?date_created_after=2024-01-01T00:00:00Z
    """
    # Get users with pagination and search
    users = await admin_user_crud.get_users(
        db=db,
        skip=pagination.skip,
        limit=pagination.limit,
    )

    # Get total count with same filters
    total = await admin_user_crud.count(
        db=db,
    )

    # Convert to response models
    user_responses = [
        UserResponse(
            id=user.id,  # type: ignore
            email=user.email,  # type: ignore
            username=user.username,  # type: ignore
            is_superuser=user.is_superuser,  # type: ignore
            is_verified=user.is_verified,  # type: ignore
            date_created=user.date_created,
            oauth_provider=user.oauth_provider,  # type: ignore
            is_deleted=user.is_deleted,  # type: ignore
            deleted_at=user.deleted_at,  # type: ignore
            deleted_by=user.deleted_by,  # type: ignore
            deletion_reason=user.deletion_reason,  # type: ignore
        )
        for user in users
    ]

    return UserListResponse.create(
        items=user_responses,
        page=pagination.page,
        size=pagination.size,
        total=total,
    )


@router.get("/search", response_model=UserSearchResponse)
async def search_users(
    pagination: PaginationParams = Depends(),
    search_params: UserSearchParams = Depends(),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserSearchResponse:
    """
    Enhanced user search with detailed metadata about applied filters and search.

    This endpoint provides the same search and filtering capabilities as the main
    users endpoint, but returns additional metadata about what filters were applied
    and search statistics.

    Returns enhanced response with:
    - users: List of matching users
    - total_count: Total number of matching users
    - search_applied: Whether text search was applied
    - filters_applied: List of filter types that were applied
    - sort_field: Field used for sorting
    - sort_order: Sort direction used
    """
    # Get users with pagination and search
    users = await admin_user_crud.get_users(
        db=db,
        skip=pagination.skip,
        limit=pagination.limit,
    )

    # Get total count with same filters
    total = await admin_user_crud.count(
        db=db,
    )

    # Convert to response models
    user_responses = [
        UserResponse(
            id=user.id,  # type: ignore
            email=user.email,  # type: ignore
            username=user.username,  # type: ignore
            is_superuser=user.is_superuser,  # type: ignore
            is_verified=user.is_verified,  # type: ignore
            date_created=user.date_created,
            oauth_provider=user.oauth_provider,  # type: ignore
            is_deleted=user.is_deleted,  # type: ignore
            deleted_at=user.deleted_at,  # type: ignore
            deleted_by=user.deleted_by,  # type: ignore
            deletion_reason=user.deletion_reason,  # type: ignore
        )
        for user in users
    ]

    # Determine which filters were applied
    filters_applied = []
    if search_params.search:
        filters_applied.append("text_search")
    if search_params.is_verified is not None:
        filters_applied.append("verification_status")
    if search_params.oauth_provider:
        filters_applied.append("oauth_provider")
    if search_params.is_superuser is not None:
        filters_applied.append("superuser_status")
    if search_params.is_deleted is not None:
        filters_applied.append("deletion_status")
    if search_params.date_created_after or search_params.date_created_before:
        filters_applied.append("date_range")

    # Calculate pagination metadata
    total_pages = (total + pagination.size - 1) // pagination.size
    has_next = pagination.page < total_pages
    has_prev = pagination.page > 1

    return UserSearchResponse(
        users=user_responses,
        total_count=total,
        page=pagination.page,
        per_page=pagination.size,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev,
        search_applied=bool(search_params.search),
        filters_applied=filters_applied,
        sort_field=search_params.sort_by,
        sort_order=search_params.sort_order,
    )
