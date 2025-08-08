"""
Admin API endpoints.

This module provides admin-only API endpoints for user management and system administration.
All endpoints require superuser privileges.
"""

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.admin import require_superuser
from app.crud.system.admin import admin_user_crud
from app.database.database import get_db
from app.schemas.admin.admin import (
    AdminBulkOperationRequest,
    AdminBulkOperationResponse,
    AdminUserCreate,
    AdminUserListResponse,
    AdminUserResponse,
    AdminUserStatistics,
    AdminUserToggleResponse,
    AdminUserUpdate,
)
from app.schemas.auth.user import UserResponse
from app.utils.pagination import PaginatedResponse, PaginationParams

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    pagination: PaginationParams = Depends(),
    is_superuser: bool | None = Query(None, description="Filter by superuser status"),
    is_verified: bool | None = Query(None, description="Filter by verification status"),
    is_deleted: bool | None = Query(None, description="Filter by deletion status"),
    oauth_provider: str | None = Query(None, description="Filter by OAuth provider"),
    current_admin: UserResponse = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[AdminUserResponse]:
    """
    List all users with optional filtering and pagination.

    This endpoint allows admins to view all users in the system with various filters.
    """
    logger.info(
        "Admin user list requested",
        extra={
            "admin_id": str(current_admin.id),
            "page": pagination.page,
            "size": pagination.size,
        },
    )

    # Build filters
    filters: dict[str, Any] = {}
    if is_superuser is not None:
        filters["is_superuser"] = bool(is_superuser)
    if is_verified is not None:
        filters["is_verified"] = bool(is_verified)
    if is_deleted is not None:
        filters["is_deleted"] = bool(is_deleted)
    if oauth_provider is not None:
        filters["oauth_provider"] = oauth_provider

    # Get users with pagination
    users = await admin_user_crud.get_users(
        db=db,
        skip=pagination.skip,
        limit=pagination.limit,
        is_superuser=is_superuser,
        is_verified=is_verified,
        is_deleted=is_deleted,
        oauth_provider=oauth_provider,
    )

    # Get total count with same filters
    total = await admin_user_crud.count(db, filters=filters)

    # Convert to response models
    user_responses = [
        AdminUserResponse(
            id=user.id,  # type: ignore
            email=user.email,  # type: ignore
            username=user.username,  # type: ignore
            is_superuser=user.is_superuser,  # type: ignore
            is_verified=user.is_verified,  # type: ignore
            is_deleted=user.is_deleted,  # type: ignore
            created_at=user.created_at,  # type: ignore
            oauth_provider=user.oauth_provider,  # type: ignore
            oauth_id=user.oauth_id,  # type: ignore
            oauth_email=user.oauth_email,  # type: ignore
            deletion_requested_at=user.deletion_requested_at,  # type: ignore
            deletion_confirmed_at=user.deletion_confirmed_at,  # type: ignore
            deletion_scheduled_for=user.deletion_scheduled_for,  # type: ignore
        )
        for user in users
    ]

    return AdminUserListResponse.create(
        items=user_responses,
        page=pagination.page,
        size=pagination.size,
        total=total,
    )


@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_user(
    user_id: UUID,
    current_admin: UserResponse = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
) -> AdminUserResponse:
    """
    Get a specific user by ID.

    This endpoint allows admins to view detailed information about a specific user.
    """
    logger.info(
        "Admin user details requested",
        extra={"admin_id": str(current_admin.id), "user_id": str(user_id)},
    )

    user = await admin_user_crud.get(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return AdminUserResponse(
        id=user.id,  # type: ignore
        email=user.email,  # type: ignore
        username=user.username,  # type: ignore
        is_superuser=user.is_superuser,  # type: ignore
        is_verified=user.is_verified,  # type: ignore
        is_deleted=user.is_deleted,  # type: ignore
        created_at=user.created_at,  # type: ignore
        oauth_provider=user.oauth_provider,  # type: ignore
        oauth_id=user.oauth_id,  # type: ignore
        oauth_email=user.oauth_email,  # type: ignore
        deletion_requested_at=user.deletion_requested_at,  # type: ignore
        deletion_confirmed_at=user.deletion_confirmed_at,  # type: ignore
        deletion_scheduled_for=user.deletion_scheduled_for,  # type: ignore
    )


@router.post(
    "/users",
    response_model=AdminUserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    user_data: AdminUserCreate,
    current_admin: UserResponse = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
) -> AdminUserResponse:
    """
    Create a new user.

    This endpoint allows admins to create new users with any privileges.
    """
    logger.info(
        "Admin user creation requested",
        extra={
            "admin_id": str(current_admin.id),
            "user_email": user_data.email,
            "is_superuser": user_data.is_superuser,
        },
    )

    # Check if user already exists
    existing_user = await admin_user_crud.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    existing_username = await admin_user_crud.get_user_by_username(
        db,
        user_data.username,
    )
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username already exists",
        )

    # Convert AdminUserCreate to UserCreate
    from app.schemas.auth.user import UserCreate

    user_create = UserCreate(
        email=user_data.email,
        username=user_data.username,
        password=user_data.password,
        is_superuser=user_data.is_superuser,
    )

    user = await admin_user_crud.create_user(db, user_create)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )

    return AdminUserResponse(
        id=user.id,  # type: ignore
        email=user.email,  # type: ignore
        username=user.username,  # type: ignore
        is_superuser=user.is_superuser,  # type: ignore
        is_verified=user.is_verified,  # type: ignore
        is_deleted=user.is_deleted,  # type: ignore
        created_at=user.created_at,  # type: ignore
        oauth_provider=user.oauth_provider,  # type: ignore
        oauth_id=user.oauth_id,  # type: ignore
        oauth_email=user.oauth_email,  # type: ignore
        deletion_requested_at=user.deletion_requested_at,  # type: ignore
        deletion_confirmed_at=user.deletion_confirmed_at,  # type: ignore
        deletion_scheduled_for=user.deletion_scheduled_for,  # type: ignore
    )


@router.put("/users/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: UUID,
    user_data: AdminUserUpdate,
    current_admin: UserResponse = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
) -> AdminUserResponse:
    """
    Update a user.

    This endpoint allows admins to update user information and privileges.
    """
    logger.info(
        "Admin user update requested",
        extra={"admin_id": str(current_admin.id), "user_id": str(user_id)},
    )

    # Check if user exists
    existing_user = await admin_user_crud.get(db, user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check for email conflicts if email is being updated
    if user_data.email and user_data.email != existing_user.email:
        email_user = await admin_user_crud.get_user_by_email(db, user_data.email)
        if email_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

    # Check for username conflicts if username is being updated
    if user_data.username and user_data.username != existing_user.username:
        username_user = await admin_user_crud.get_user_by_username(
            db,
            user_data.username,
        )
        if username_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this username already exists",
            )

    user = await admin_user_crud.update_user(db, user_id, user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )

    return AdminUserResponse(
        id=user.id,  # type: ignore
        email=user.email,  # type: ignore
        username=user.username,  # type: ignore
        is_superuser=user.is_superuser,  # type: ignore
        is_verified=user.is_verified,  # type: ignore
        is_deleted=user.is_deleted,  # type: ignore
        created_at=user.created_at,  # type: ignore
        oauth_provider=user.oauth_provider,  # type: ignore
        oauth_id=user.oauth_id,  # type: ignore
        oauth_email=user.oauth_email,  # type: ignore
        deletion_requested_at=user.deletion_requested_at,  # type: ignore
        deletion_confirmed_at=user.deletion_confirmed_at,  # type: ignore
        deletion_scheduled_for=user.deletion_scheduled_for,  # type: ignore
    )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    current_admin: UserResponse = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a user.

    This endpoint allows admins to delete users from the system.
    """
    logger.info(
        "Admin user deletion requested",
        extra={"admin_id": str(current_admin.id), "user_id": str(user_id)},
    )

    # Prevent admins from deleting their own account
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    # Check if user exists
    existing_user = await admin_user_crud.get(db, user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    success = await admin_user_crud.delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user",
        )


@router.post(
    "/users/{user_id}/toggle-superuser",
    response_model=AdminUserToggleResponse,
)
async def toggle_superuser_status(
    user_id: UUID,
    current_admin: UserResponse = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
) -> AdminUserToggleResponse:
    """
    Toggle superuser status for a user.

    This endpoint allows admins to grant or revoke superuser privileges.
    """
    logger.info(
        "Admin superuser toggle requested",
        extra={"admin_id": str(current_admin.id), "user_id": str(user_id)},
    )

    # Prevent admins from modifying their own superuser status
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own superuser status",
        )

    user = await admin_user_crud.toggle_superuser_status(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return AdminUserToggleResponse(
        user_id=user.id,  # type: ignore
        field="is_superuser",
        new_value=user.is_superuser,  # type: ignore
        message=f"Superuser status {'enabled' if user.is_superuser else 'disabled'} successfully",
    )


@router.post(
    "/users/{user_id}/toggle-verification",
    response_model=AdminUserToggleResponse,
)
async def toggle_verification_status(
    user_id: UUID,
    current_admin: UserResponse = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
) -> AdminUserToggleResponse:
    """
    Toggle verification status for a user.

    This endpoint allows admins to verify or unverify users.
    """
    logger.info(
        "Admin verification toggle requested",
        extra={"admin_id": str(current_admin.id), "user_id": str(user_id)},
    )

    user = await admin_user_crud.toggle_verification_status(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return AdminUserToggleResponse(
        user_id=user.id,  # type: ignore
        field="is_verified",
        new_value=user.is_verified,  # type: ignore
        message=f"Verification status {'enabled' if user.is_verified else 'disabled'} successfully",
    )


@router.post("/users/{user_id}/force-delete", status_code=status.HTTP_204_NO_CONTENT)
async def force_delete_user(
    user_id: UUID,
    current_admin: UserResponse = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Force delete a user (permanent deletion).

    This endpoint allows admins to permanently delete users from the system.
    Use with caution as this action cannot be undone.
    """
    logger.info(
        "Admin force delete requested",
        extra={"admin_id": str(current_admin.id), "user_id": str(user_id)},
    )

    # Check if user exists
    existing_user = await admin_user_crud.get(db, user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    success = await admin_user_crud.force_delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to force delete user",
        )


@router.get("/statistics", response_model=AdminUserStatistics)
async def get_user_statistics(
    current_admin: UserResponse = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
) -> AdminUserStatistics:
    """
    Get user statistics for admin dashboard.

    This endpoint provides statistics about users in the system.
    """
    logger.info("Admin statistics requested", extra={"admin_id": str(current_admin.id)})

    stats = await admin_user_crud.get_user_statistics(db)
    return AdminUserStatistics(**stats)


@router.post("/bulk-operations", response_model=AdminBulkOperationResponse)
async def bulk_operations(
    request: AdminBulkOperationRequest,
    current_admin: UserResponse = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
) -> AdminBulkOperationResponse:
    """
    Perform bulk operations on users.

    This endpoint allows admins to perform operations on multiple users at once.
    """
    logger.info(
        "Admin bulk operation requested",
        extra={"admin_id": str(current_admin.id), "operation": request.operation},
    )

    successful = 0
    failed = 0
    failed_user_ids = []

    for user_id in request.user_ids:
        try:
            if request.operation == "verify":
                user = await admin_user_crud.toggle_verification_status(db, user_id)
                if user and not user.is_verified:
                    # If user was not verified, toggle again to verify them
                    user = await admin_user_crud.toggle_verification_status(db, user_id)
                if user:
                    successful += 1
                else:
                    failed += 1
                    failed_user_ids.append(user_id)
            elif request.operation == "unverify":
                user = await admin_user_crud.toggle_verification_status(db, user_id)
                if user and user.is_verified:
                    # If user was verified, toggle again to unverify them
                    user = await admin_user_crud.toggle_verification_status(db, user_id)
                if user:
                    successful += 1
                else:
                    failed += 1
                    failed_user_ids.append(user_id)
            else:
                failed += 1
                failed_user_ids.append(user_id)
        except Exception:
            failed += 1
            failed_user_ids.append(user_id)

    return AdminBulkOperationResponse(
        operation=request.operation,
        total_users=len(request.user_ids),
        successful=successful,
        failed=failed,
        failed_user_ids=failed_user_ids,
    )
