from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud import user as crud_user
from app.database.database import get_db
from app.schemas.user import TokenData, UserListResponse, UserResponse
from app.utils.pagination import PaginatedResponse, PaginationParams

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> UserResponse:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    if token_data.email is None:
        raise credentials_exception

    user = crud_user.get_user_by_email_sync(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user


@router.get("/me", response_model=UserResponse)
async def read_current_user(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    return current_user


@router.get("", response_model=UserListResponse)
async def list_users(
    pagination: PaginationParams = Depends(),
    is_verified: Optional[bool] = Query(
        None, description="Filter by verification status"
    ),
    oauth_provider: Optional[str] = Query(None, description="Filter by OAuth provider"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedResponse[UserResponse]:
    """
    List users with optional filtering and pagination.

    This endpoint allows authenticated users to view other users in the system.
    Note: This is a basic listing - for admin operations, use the admin endpoints.
    """
    # Get users with pagination
    users = await crud_user.get_users(
        db=db,
        skip=pagination.skip,
        limit=pagination.limit,
        is_verified=is_verified,
        oauth_provider=oauth_provider,
    )

    # Get total count with same filters
    total = await crud_user.count_users(
        db=db,
        is_verified=is_verified,
        oauth_provider=oauth_provider,
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
        )
        for user in users
    ]

    return UserListResponse.create(
        items=user_responses,
        page=pagination.page,
        size=pagination.size,
        total=total,
    )
