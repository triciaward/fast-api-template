"""
Admin HTML views for web-based administration.

This module provides HTML-based admin interfaces using Jinja2 templates.
All endpoints require superuser privileges.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.templating import _TemplateResponse

from app.core.admin import require_superuser
from app.crud.api_key import (  # type: ignore
    count_all_api_keys_sync,
    create_api_key_sync,
    deactivate_api_key_sync,
    get_all_api_keys_sync,
    get_api_key_by_id_sync,
    rotate_api_key_sync,
)
from app.database.database import get_db_sync
from app.schemas.user import APIKeyCreate, UserResponse

logger = logging.getLogger(__name__)

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="app/templates")


async def admin_api_keys_view(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    current_admin: UserResponse = Depends(require_superuser),
    db: Session = Depends(get_db_sync),
) -> _TemplateResponse:
    """
    Admin view for managing API keys.

    This endpoint renders an HTML page showing all API keys in the system
    with options to create, rotate, and revoke keys.
    """
    logger.info(
        "Admin API keys view accessed",
        extra={"admin_id": str(current_admin.id), "page": page},
    )

    # Pagination settings
    page_size = 20
    skip = (page - 1) * page_size

    # Get API keys with pagination
    api_keys = get_all_api_keys_sync(
        db=db,
        skip=skip,
        limit=page_size,
    )

    # Get total count
    total_count = count_all_api_keys_sync(db=db)
    total_pages = (total_count + page_size - 1) // page_size

    # Convert to response models for template
    from app.schemas.user import APIKeyResponse

    api_key_responses = [APIKeyResponse.model_validate(key) for key in api_keys]

    return templates.TemplateResponse(
        "admin/api_keys.html",
        {
            "request": request,
            "current_user": current_admin,
            "api_keys": api_key_responses,
            "total_count": total_count,
            "current_page": page,
            "total_pages": total_pages,
            "now": datetime.utcnow(),
        },
    )


async def admin_create_api_key(
    request: Request,
    label: str = Form(..., description="API key label"),
    scopes: str = Form("", description="Comma-separated scopes"),
    expires_at: Optional[str] = Form(None, description="Expiration date"),
    current_admin: UserResponse = Depends(require_superuser),
    db: Session = Depends(get_db_sync),
) -> RedirectResponse:
    """
    Create a new API key via admin interface.
    """
    logger.info(
        "Admin creating API key",
        extra={
            "admin_id": str(current_admin.id),
            "label": label,
            "scopes": scopes,
        },
    )

    try:
        # Parse scopes
        scope_list = (
            [s.strip() for s in scopes.split(",") if s.strip()] if scopes else []
        )

        # Parse expiration date
        expires_datetime = None
        if expires_at:
            try:
                expires_datetime = datetime.fromisoformat(
                    expires_at.replace("Z", "+00:00")
                )
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid expiration date format",
                ) from e

        # Create API key data
        api_key_data = APIKeyCreate(
            label=label,
            scopes=scope_list,
            expires_at=expires_datetime,
        )

        # Generate the API key
        from app.core.security import generate_api_key

        raw_key = generate_api_key()

        # Create the API key in the database
        db_api_key = create_api_key_sync(
            db=db,
            api_key_data=api_key_data,
            user_id=str(current_admin.id),
            raw_key=raw_key,
        )

        logger.info(
            "API key created successfully via admin",
            extra={
                "admin_id": str(current_admin.id),
                "key_id": str(db_api_key.id),
                "label": label,
            },
        )

        # Redirect with success message
        response = RedirectResponse(
            url=(
                "/admin/api-keys?message=API key created successfully"
                "&message_type=success"
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )
        return response

    except Exception as e:
        logger.error(
            "Failed to create API key via admin",
            extra={
                "admin_id": str(current_admin.id),
                "error": str(e),
            },
        )

        # Redirect with error message
        response = RedirectResponse(
            url=(
                f"/admin/api-keys?message=Failed to create API key: {str(e)}"
                "&message_type=danger"
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )
        return response


async def admin_rotate_api_key(
    request: Request,
    key_id: str,
    current_admin: UserResponse = Depends(require_superuser),
    db: Session = Depends(get_db_sync),
) -> RedirectResponse:
    """
    Rotate an API key via admin interface.
    """
    logger.info(
        "Admin rotating API key",
        extra={
            "admin_id": str(current_admin.id),
            "key_id": key_id,
        },
    )

    try:
        # Rotate the key
        result = rotate_api_key_sync(
            db=db,
            key_id=key_id,
        )

        if not result[0]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found",
            )

        api_key, new_raw_key = result

        logger.info(
            "API key rotated successfully via admin",
            extra={
                "admin_id": str(current_admin.id),
                "key_id": key_id,
                "label": api_key.label if api_key else "Unknown",
            },
        )

        # Redirect with success message
        response = RedirectResponse(
            url=(
                f"/admin/api-keys?message=API key "
                f"'{api_key.label if api_key else 'Unknown'}' "
                f"rotated successfully. New key: {new_raw_key}&message_type=success"
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )
        return response

    except Exception as e:
        logger.error(
            "Failed to rotate API key via admin",
            extra={
                "admin_id": str(current_admin.id),
                "key_id": key_id,
                "error": str(e),
            },
        )

        # Redirect with error message
        response = RedirectResponse(
            url=(
                f"/admin/api-keys?message=Failed to rotate API key: {str(e)}"
                "&message_type=danger"
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )
        return response


async def admin_revoke_api_key(
    request: Request,
    key_id: str,
    current_admin: UserResponse = Depends(require_superuser),
    db: Session = Depends(get_db_sync),
) -> RedirectResponse:
    """
    Revoke an API key via admin interface.
    """
    logger.info(
        "Admin revoking API key",
        extra={
            "admin_id": str(current_admin.id),
            "key_id": key_id,
        },
    )

    try:
        # Get the key first to get the label for the message
        api_key = get_api_key_by_id_sync(db=db, key_id=key_id)
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found",
            )

        # Deactivate the key
        success = deactivate_api_key_sync(
            db=db,
            key_id=key_id,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found",
            )

        logger.info(
            "API key revoked successfully via admin",
            extra={
                "admin_id": str(current_admin.id),
                "key_id": key_id,
                "label": api_key.label if api_key else "Unknown",
            },
        )

        # Redirect with success message
        response = RedirectResponse(
            url=f"/admin/api-keys?message=API key '{api_key.label if api_key else 'Unknown'}' revoked successfully&message_type=success",
            status_code=status.HTTP_303_SEE_OTHER,
        )
        return response

    except Exception as e:
        logger.error(
            "Failed to revoke API key via admin",
            extra={
                "admin_id": str(current_admin.id),
                "key_id": key_id,
                "error": str(e),
            },
        )

        # Redirect with error message
        response = RedirectResponse(
            url=f"/admin/api-keys?message=Failed to revoke API key: {str(e)}&message_type=danger",
            status_code=status.HTTP_303_SEE_OTHER,
        )
        return response
