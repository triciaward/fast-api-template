import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api.api_v1.endpoints.users import get_current_user
from app.core.logging_config import get_auth_logger
from app.crud import refresh_token as crud_refresh_token
from app.crud import user as crud_user
from app.database.database import get_db_sync
from app.schemas.user import (
    RefreshTokenResponse,
    SessionInfo,
    SessionListResponse,
    UserResponse,
)
from app.services.audit import log_logout

router = APIRouter()
logger = get_auth_logger()


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: Request,
    db: Session = Depends(get_db_sync),
) -> RefreshTokenResponse:
    """Refresh an access token using a valid refresh token from cookies."""
    logger.info("Token refresh attempt")

    try:
        # Get refresh token from cookie
        from app.services.refresh_token import (
            get_refresh_token_from_cookie,
            refresh_access_token,
        )

        refresh_token_value = get_refresh_token_from_cookie(request)
        if not refresh_token_value:
            logger.warning("Token refresh failed - no refresh token in cookie")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No refresh token provided",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Refresh the access token
        result = refresh_access_token(db, refresh_token_value)
        if not result:
            logger.warning("Token refresh failed - invalid refresh token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token, expires_at = result
        expires_in = int((expires_at - datetime.utcnow()).total_seconds())

        logger.info("Token refresh successful")
        return RefreshTokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Token refresh failed with unexpected error",
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed. Please try again later.",
        )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db_sync),
) -> dict:
    """Logout user by revoking the current refresh token."""
    logger.info("Logout attempt")

    try:
        from app.services.refresh_token import (
            clear_refresh_token_cookie,
            get_refresh_token_from_cookie,
            revoke_session,
        )

        # Get refresh token from cookie
        refresh_token_value = get_refresh_token_from_cookie(request)
        user = None

        if refresh_token_value:
            # Get user from refresh token for audit logging
            from app.crud import verify_refresh_token_in_db

            db_token = verify_refresh_token_in_db(db, refresh_token_value)
            if db_token:
                user = crud_user.get_user_by_id_sync(db, str(db_token.user_id))

            # Revoke the session
            revoke_session(db, refresh_token_value)
            logger.info("Session revoked during logout")

        # Clear the cookie
        clear_refresh_token_cookie(response)

        # Log logout event if we have user info
        if user:
            await log_logout(db, request, user)

        logger.info("Logout successful")
        return {"message": "Successfully logged out"}

    except Exception as e:
        logger.error(
            "Logout failed with unexpected error",
            error=str(e),
            exc_info=True,
        )
        # Still clear the cookie even if revocation fails
        from app.services.refresh_token import clear_refresh_token_cookie

        clear_refresh_token_cookie(response)
        return {"message": "Successfully logged out"}


@router.get("/sessions", response_model=SessionListResponse)
async def get_user_sessions(
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db_sync),
) -> SessionListResponse:
    """Get all active sessions for the current user."""
    logger.info("Get user sessions request", user_id=str(current_user.id))

    try:
        from app.crud import get_user_sessions as crud_get_user_sessions
        from app.services.refresh_token import get_refresh_token_from_cookie

        # Get current session ID
        current_refresh_token = get_refresh_token_from_cookie(request)
        current_session_id = None

        if current_refresh_token:
            from app.crud import verify_refresh_token_in_db

            db_token = verify_refresh_token_in_db(db, current_refresh_token)
            if db_token:
                current_session_id = db_token.id

                # Get all user sessions
        sessions = crud_get_user_sessions(
            db, current_user.id, current_session_id  # type: ignore[arg-type]
        )

        # Convert to response format
        session_info_list = []
        for session in sessions:
            session_info = SessionInfo(
                id=session.id,  # type: ignore[arg-type]
                created_at=session.created_at,  # type: ignore[arg-type]
                device_info=session.device_info,  # type: ignore[arg-type]
                ip_address=session.ip_address,  # type: ignore[arg-type]
                is_current=getattr(session, "is_current", False),
            )
            session_info_list.append(session_info)

        logger.info(
            "User sessions retrieved successfully",
            user_id=str(current_user.id),
            session_count=len(session_info_list),
        )

        return SessionListResponse(
            sessions=session_info_list,
            total_sessions=len(session_info_list),
        )

    except Exception as e:
        logger.error(
            "Failed to get user sessions",
            user_id=str(current_user.id),
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions. Please try again later.",
        )


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db_sync),
) -> dict:
    """Revoke a specific session for the current user."""
    logger.info(
        "Revoke session request",
        user_id=str(current_user.id),
        session_id=session_id,
    )

    try:
        from app.crud import revoke_refresh_token

        # Validate session ID format
        try:
            session_uuid = uuid.UUID(session_id)
        except ValueError:
            logger.warning("Invalid session ID format", session_id=session_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid session ID format",
            )

        # Revoke the session
        success = revoke_refresh_token(db, session_uuid)
        if not success:
            logger.warning(
                "Session not found or already revoked",
                user_id=str(current_user.id),
                session_id=session_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or already revoked",
            )

        logger.info(
            "Session revoked successfully",
            user_id=str(current_user.id),
            session_id=session_id,
        )

        return {"message": "Session revoked successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to revoke session",
            user_id=str(current_user.id),
            session_id=session_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke session. Please try again later.",
        )


@router.delete("/sessions")
async def revoke_all_sessions(
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db_sync),
) -> dict:
    """Revoke all refresh tokens for the current user."""
    logger.info(
        "User revoking all sessions",
        user_id=str(current_user.id),
        email=current_user.email,
    )

    # Get the actual user object from database
    db_user = crud_user.get_user_by_id_sync(db, str(current_user.id))
    if not db_user:
        logger.error("User not found in database", user_id=str(current_user.id))
        raise HTTPException(
            status_code=500, detail="User not found. Please try again later."
        )

    # Revoke all sessions for the user
    revoked_count = crud_refresh_token.revoke_all_user_sessions(db, current_user.id)

    # Log the action
    await log_logout(
        db=db,
        request=request,
        user=db_user,
    )

    logger.info(
        "All sessions revoked successfully",
        user_id=str(current_user.id),
        revoked_count=revoked_count,
    )

    return {
        "message": f"All sessions revoked successfully. {revoked_count} sessions were active."
    }
