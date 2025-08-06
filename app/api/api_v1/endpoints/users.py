from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud import api_key as crud_api_key
from app.crud import user as crud_user
from app.crud.admin import AdminUserCRUD
from app.database.database import get_db
from app.schemas.user import (
    APIKeyUser,
    DeletedUserListResponse,
    DeletedUserResponse,
    DeletedUserSearchResponse,
    RestoreUserResponse,
    SoftDeleteRequest,
    SoftDeleteResponse,
    TokenData,
    UserListResponse,
    UserResponse,
    UserSearchResponse,
)
from app.utils.pagination import PaginatedResponse, PaginationParams
from app.utils.search_filter import DeletedUserSearchParams, UserSearchParams

router = APIRouter()

# Initialize admin CRUD for user operations
admin_user_crud = AdminUserCRUD()


def utc_now() -> datetime:
    """Get current UTC datetime (replaces deprecated datetime.utcnow())."""
    return datetime.now(timezone.utc)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db),
) -> UserResponse:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM],
        )
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError as e:
        raise credentials_exception from e

    if token_data.email is None:
        raise credentials_exception

    user = crud_user.get_user_by_email_sync(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user


async def get_api_key_user(
    request: Request,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> APIKeyUser:
    """Authenticate user via API key from Authorization header."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if it's a Bearer token
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Use 'Bearer <api_key>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract the API key
    api_key = authorization[7:]  # Remove "Bearer " prefix

    # Verify the API key
    db_api_key = crud_api_key.verify_api_key_in_db_sync(db, api_key)
    if not db_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if key is active and not expired
    if not db_api_key.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if db_api_key.expires_at and db_api_key.expires_at < utc_now():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Log successful API key usage
    from app.services.audit import log_api_key_usage_sync

    log_api_key_usage_sync(
        db=db,
        request=request,
        api_key_id=str(db_api_key.id),
        key_label=getattr(db_api_key, "label", ""),
        user_id=str(db_api_key.user_id) if db_api_key.user_id else None,
    )

    # Return API key user object
    return APIKeyUser(
        id=db_api_key.id,  # type: ignore
        scopes=db_api_key.scopes,  # type: ignore
        user_id=db_api_key.user_id,  # type: ignore
        key_id=db_api_key.id,  # type: ignore
    )


def require_api_scope(required_scope: str):
    """Dependency to check if API key has required scope."""

    def scope_checker(
        api_key_user: APIKeyUser = Depends(get_api_key_user),
    ) -> APIKeyUser:
        if required_scope not in api_key_user.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"API key missing required scope: {required_scope}",
            )
        return api_key_user

    return scope_checker


@router.get("/me", response_model=UserResponse)
async def read_current_user(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    return current_user


@router.get("/me/api-key", response_model=APIKeyUser)
async def read_current_user_api_key(
    api_key_user: APIKeyUser = Depends(get_api_key_user),
) -> APIKeyUser:
    """Get current user information via API key authentication."""
    return api_key_user


@router.get("", response_model=UserListResponse)
async def list_users(
    pagination: PaginationParams = Depends(),
    search_params: UserSearchParams = Depends(),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
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
            date_created=user.date_created,  # type: ignore
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
    db: Session = Depends(get_db),
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
            date_created=user.date_created,  # type: ignore
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


# Soft Delete Endpoints
@router.delete("/{user_id}/soft", response_model=SoftDeleteResponse)
async def soft_delete_user(
    user_id: str,
    delete_request: SoftDeleteRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
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
    user = crud_user.get_user_by_id_sync(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found",
        )

    if user.is_deleted:  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is already deleted",
        )

    # Perform soft delete
    success = await crud_user.soft_delete_user(db=db, user_id=user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to soft delete user",
        )

    # Get the updated user to return deletion details
    updated_user = crud_user.get_user_by_id_sync(db, user_id)

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
    db: Session = Depends(get_db),
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
    user = crud_user.get_user_by_id_sync(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found",
        )

    if not user.is_deleted:  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is not deleted",
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
        user_id=user.id,  # type: ignore
        restored_at=utc_now(),
    )


@router.get("/deleted", response_model=DeletedUserListResponse)
async def list_deleted_users(
    pagination: PaginationParams = Depends(),
    search_params: DeletedUserSearchParams = Depends(),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
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
            date_created=user.date_created,  # type: ignore
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
    db: Session = Depends(get_db),
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
            date_created=user.date_created,  # type: ignore
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
    db: Session = Depends(get_db),
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
    user = crud_user.get_user_by_id_sync(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found",
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
