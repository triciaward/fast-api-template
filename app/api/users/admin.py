"""
Administrative user operations.

This module provides endpoints for administrative operations on users,
including soft delete, restore, permanent delete, and management of
deleted users.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.users.auth import get_current_user, utc_now
from app.crud.auth import user as crud_user
from app.crud.system.admin import AdminUserCRUD
from app.database.database import get_db
from app.schemas.auth.user import (
    DeletedUserListResponse,
    DeletedUserResponse,
    DeletedUserSearchResponse,
    RestoreUserResponse,
    SoftDeleteRequest,
    SoftDeleteResponse,
    UserResponse,
)
from app.utils.pagination import PaginatedResponse, PaginationParams
from app.utils.search_filter import DeletedUserSearchParams

router = APIRouter()

# Initialize admin CRUD for user operations
admin_user_crud = AdminUserCRUD()


@router.delete("/{user_id}/soft", response_model=SoftDeleteResponse)
async def soft_delete_user(
    user_id: str,
    delete_request: SoftDeleteRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SoftDeleteResponse:
    """
    Soft delete a user by marking it as deleted.

    This endpoint marks a user as deleted without actually removing the record
    from the database. The user will be hidden from normal queries but can be
    restored later if needed.

    Args:
        user_id: ID of the user to soft delete
        delete_request: Request containing optional deletion reason
        current_user: Currently authenticated user (who is performing the deletion)

    Returns:
        SoftDeleteResponse: Confirmation of the soft delete operation
    """
    # Check if user exists and is not already deleted
    user = await crud_user.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already deleted",
        )

    # Perform soft delete
    success = await crud_user.soft_delete_user(db=db, user_id=user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to soft delete user",
        )

    # Get the updated user to return deletion details
    updated_user = await crud_user.get_user_by_id(db, user_id)

    return SoftDeleteResponse(
        message="User soft deleted successfully",
        user_id=updated_user.id,  # type: ignore
        deleted_at=updated_user.deleted_at,  # type: ignore
        deleted_by=updated_user.deleted_by,  # type: ignore
        reason=updated_user.deletion_reason,  # type: ignore
    )


@router.post("/{user_id}/restore", response_model=RestoreUserResponse)
async def restore_user(
    user_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RestoreUserResponse:
    """
    Restore a soft-deleted user.

    This endpoint restores a previously soft-deleted user, making them visible
    again in normal queries.

    Args:
        user_id: ID of the user to restore
        current_user: Currently authenticated user (who is performing the restoration)

    Returns:
        RestoreUserResponse: Confirmation of the restore operation
    """
    # Check if user exists and is deleted
    user = await crud_user.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not deleted",
        )

    # Perform restore
    success = await crud_user.restore_user(db=db, user_id=user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restore user",
        )

    return RestoreUserResponse(
        message="User restored successfully",
        user_id=user.id,  # type: ignore[arg-type]
        restored_at=utc_now(),
    )


@router.get("/deleted", response_model=DeletedUserListResponse)
async def list_deleted_users(
    pagination: PaginationParams = Depends(),
    search_params: DeletedUserSearchParams = Depends(),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[DeletedUserResponse]:
    """
    List soft-deleted users with filtering and pagination.

    This endpoint allows viewing users that have been soft deleted, with
    filtering capabilities for audit and recovery purposes.

    Filter Options:
    - deleted_by: Filter by user who performed the deletion
    - deletion_reason: Search in deletion reason field
    - deleted_after: Filter users deleted after this date
    - deleted_before: Filter users deleted before this date
    - sort_by: Field to sort by
    - sort_order: Sort order (asc or desc)

    Examples:
    - ?deleted_by=user-uuid&sort_by=deleted_at&sort_order=desc
    - ?deletion_reason=spam&deleted_after=2024-01-01T00:00:00Z
    """
    # Get deleted users with pagination and search
    users = await admin_user_crud.get_deleted_users(
        db=db,
        skip=pagination.skip,
        limit=pagination.limit,
    )

    # Get total count with same filters
    total = await admin_user_crud.count_deleted_users(
        db=db,
    )

    # Convert to response models
    user_responses = [
        DeletedUserResponse(
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

    return DeletedUserListResponse.create(
        items=user_responses,
        page=pagination.page,
        size=pagination.size,
        total=total,
    )


@router.get("/deleted/search", response_model=DeletedUserSearchResponse)
async def search_deleted_users(
    pagination: PaginationParams = Depends(),
    search_params: DeletedUserSearchParams = Depends(),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DeletedUserSearchResponse:
    """
    Enhanced search for soft-deleted users with detailed metadata.

    This endpoint provides the same search and filtering capabilities as the main
    deleted users endpoint, but returns additional metadata about what filters
    were applied and search statistics.

    Returns enhanced response with:
    - users: List of matching deleted users
    - total_count: Total number of matching deleted users
    - filters_applied: List of filter types that were applied
    - sort_field: Field used for sorting
    - sort_order: Sort direction used
    """
    # Get deleted users with pagination and search
    users = await admin_user_crud.get_deleted_users(
        db=db,
        skip=pagination.skip,
        limit=pagination.limit,
    )

    # Get total count with same filters
    total = await admin_user_crud.count_deleted_users(
        db=db,
    )

    # Convert to response models
    user_responses = [
        DeletedUserResponse(
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
    if search_params.deletion_reason:
        filters_applied.append("deletion_reason_search")
    if search_params.deleted_by:
        filters_applied.append("deleted_by")
    if search_params.deleted_after or search_params.deleted_before:
        filters_applied.append("deletion_date_range")

    # Calculate pagination metadata
    total_pages = (total + pagination.size - 1) // pagination.size
    has_next = pagination.page < total_pages
    has_prev = pagination.page > 1

    return DeletedUserSearchResponse(
        users=user_responses,
        total_count=total,
        page=pagination.page,
        per_page=pagination.size,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev,
        filters_applied=filters_applied,
        sort_field=search_params.sort_by,
        sort_order=search_params.sort_order,
    )


@router.delete("/{user_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
async def permanently_delete_user(
    user_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Permanently delete a user from the database.

    ⚠️ WARNING: This operation is irreversible and will permanently remove
    the user record from the database. Use with extreme caution.

    Args:
        user_id: ID of the user to permanently delete
        current_user: Currently authenticated user (who is performing the deletion)

    Returns:
        None: 204 No Content on success
    """
    # Check if user exists
    user = await crud_user.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Perform permanent delete
    success = await crud_user.permanently_delete_user(db=db, user_id=user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to permanently delete user",
        )

    # Return 204 No Content
    return
