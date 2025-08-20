"""
User authentication dependencies for API endpoints.

This module provides authentication and authorization dependencies used
across the user API endpoints.
"""

from collections.abc import Callable
from datetime import datetime, timezone

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.auth import api_key as crud_api_key
from app.crud.auth import user as crud_user
from app.database.database import get_db
from app.schemas.auth.user import APIKeyUser, TokenData, UserResponse


def utc_now() -> datetime:
    """Get current UTC datetime (replaces deprecated datetime.utcnow())."""
    return datetime.now(timezone.utc)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        TokenData(email=None)
    except JWTError as e:
        raise credentials_exception from e

    # Fetch by user id (subject)
    user = await crud_user.get_user_by_id(db, user_id=str(user_id))
    if user is None:
        raise credentials_exception
    # Convert to response schema
    from app.schemas.auth.user import UserResponse

    return UserResponse.model_validate(user)


async def get_api_key_user(
    request: Request,
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
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
    db_api_key = await crud_api_key.verify_api_key_in_db(db, api_key)
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
    from app.services.monitoring.audit import log_api_key_usage

    await log_api_key_usage(
        db=db,
        request=request,
        api_key_id=str(db_api_key.id),
        key_label=getattr(db_api_key, "label", ""),
        user_id=str(db_api_key.user_id) if db_api_key.user_id else None,
    )

    # Return API key user object
    return APIKeyUser.model_validate(db_api_key)


def require_api_scope(required_scope: str) -> Callable[[APIKeyUser], APIKeyUser]:
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
