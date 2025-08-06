from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.api_v1.endpoints.users import get_current_user
from app.core.logging_config import get_auth_logger
from app.crud import api_key as crud_api_key
from app.database.database import get_db_sync
from app.schemas.user import (
    APIKeyCreate,
    APIKeyCreateResponse,
    APIKeyListResponse,
    APIKeyResponse,
    APIKeyRotateResponse,
    UserResponse,
)
from app.utils.pagination import PaginationParams

router = APIRouter()
logger = get_auth_logger()


@router.post("/api-keys", response_model=APIKeyCreateResponse, status_code=201)
async def create_api_key(
    api_key_data: APIKeyCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db_sync),
) -> APIKeyCreateResponse:
    """Create a new API key for the current user."""
    logger.info(
        "User creating API key",
        user_id=str(current_user.id),
        email=current_user.email,
        label=api_key_data.label,
    )

    try:
        # Generate the API key
        from app.core.security import generate_api_key

        raw_key = generate_api_key()

        # Create the API key in the database
        db_api_key = crud_api_key.create_api_key_sync(
            db=db,
            api_key_data=api_key_data,
            user_id=str(current_user.id),
            raw_key=raw_key,
        )

        logger.info(
            "API key created successfully",
            user_id=str(current_user.id),
            key_id=str(db_api_key.id),
            label=api_key_data.label,
        )

        return APIKeyCreateResponse(
            api_key=db_api_key,
            raw_key=raw_key,
        )

    except Exception as e:
        logger.exception(
            "Failed to create API key",
            user_id=str(current_user.id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key",
        ) from e


@router.get("/api-keys", response_model=APIKeyListResponse)
async def list_api_keys(
    pagination: PaginationParams = Depends(),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db_sync),
) -> APIKeyListResponse:
    """List all API keys for the current user."""
    logger.info(
        "User listing API keys",
        user_id=str(current_user.id),
        email=current_user.email,
    )

    # Get API keys with pagination
    api_keys = crud_api_key.get_user_api_keys_sync(
        db=db,
        user_id=str(current_user.id),
        skip=pagination.skip,
        limit=pagination.limit,
    )

    # Count total API keys
    total_count = crud_api_key.count_user_api_keys_sync(
        db=db,
        user_id=str(current_user.id),
    )

    # Convert SQLAlchemy objects to Pydantic models
    api_key_responses = [APIKeyResponse.model_validate(api_key) for api_key in api_keys]

    return APIKeyListResponse.create(  # type: ignore[return-value]
        items=api_key_responses,
        page=pagination.page,
        size=pagination.limit,
        total=total_count,
    )


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_api_key(
    key_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db_sync),
) -> None:
    """Deactivate an API key."""
    logger.info(
        "User deactivating API key",
        user_id=str(current_user.id),
        email=current_user.email,
        key_id=key_id,
    )

    success = crud_api_key.deactivate_api_key_sync(
        db=db,
        key_id=key_id,
        user_id=str(current_user.id),
    )

    if not success:
        logger.warning(
            "Failed to deactivate API key - not found or not owned by user",
            user_id=str(current_user.id),
            key_id=key_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    logger.info(
        "API key deactivated successfully",
        user_id=str(current_user.id),
        key_id=key_id,
    )


@router.post("/api-keys/{key_id}/rotate", response_model=APIKeyRotateResponse)
async def rotate_api_key(
    key_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db_sync),
) -> APIKeyRotateResponse:
    """Rotate an API key by generating a new one."""
    logger.info(
        "User rotating API key",
        user_id=str(current_user.id),
        email=current_user.email,
        key_id=key_id,
    )

    result = crud_api_key.rotate_api_key_sync(
        db=db,
        key_id=key_id,
        user_id=str(current_user.id),
    )

    if not result[0]:
        logger.warning(
            "Failed to rotate API key - not found or not owned by user",
            user_id=str(current_user.id),
            key_id=key_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    api_key, new_raw_key = result

    logger.info(
        "API key rotated successfully",
        user_id=str(current_user.id),
        key_id=key_id,
    )

    if not new_raw_key:
        raise HTTPException(
            status_code=500, detail="Failed to rotate API key. Please try again later.",
        )

    return APIKeyRotateResponse(
        api_key=APIKeyResponse.model_validate(api_key),
        new_raw_key=new_raw_key,
    )
