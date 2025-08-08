from typing import NoReturn

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.users.auth import get_current_user
from app.core.config.logging_config import get_auth_logger
from app.core.security import verify_password
from app.crud.auth import user as crud_user
from app.database.database import get_db
from app.schemas.auth.user import (
    PasswordChangeRequest,
    PasswordChangeResponse,
    PasswordResetConfirmRequest,
    PasswordResetConfirmResponse,
    PasswordResetRequest,
    PasswordResetResponse,
    UserResponse,
)
from app.services import email_service, rate_limit_password_reset
from app.services.monitoring.audit import log_password_change

router = APIRouter()
logger = get_auth_logger()


@router.post("/forgot-password", response_model=PasswordResetResponse)
@rate_limit_password_reset
async def forgot_password(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
) -> PasswordResetResponse:
    """Request password reset."""
    logger.info("Password reset request", email=request.email)

    try:
        # Check if user exists
        user = await crud_user.get_user_by_email(db, email=request.email)
        if not user:
            # Don't reveal if user exists or not for security
            logger.info(
                "Password reset request for non-existent user",
                email=request.email,
            )
            return PasswordResetResponse(
                message="If an account with that email exists, a password reset link has been sent.",
                email_sent=True,
            )

        # Don't allow password reset for OAuth users
        if user.oauth_provider:
            logger.warning(
                "Password reset attempted for OAuth user",
                user_id=str(user.id),
                email=request.email,
                oauth_provider=user.oauth_provider,
            )
            return PasswordResetResponse(
                message="If an account with that email exists, a password reset link has been sent.",
                email_sent=True,
            )

        if not email_service or not email_service.is_configured():
            logger.warning(
                "Email service not configured for password reset",
                email=request.email,
            )
            return PasswordResetResponse(
                message="Password reset service temporarily unavailable. Please try again later.",
                email_sent=False,
            )

        # Create password reset token
        reset_token = await email_service.create_password_reset_token(db, str(user.id))
        if not reset_token:
            logger.error(
                "Failed to create password reset token",
                user_id=str(user.id),
                email=request.email,
            )
            return PasswordResetResponse(
                message="Failed to create password reset token. Please try again later.",
                email_sent=False,
            )

        # Send password reset email
        email_sent = email_service.send_password_reset_email(
            str(user.email),
            str(user.username),
            reset_token,
        )

        if email_sent:
            logger.info(
                "Password reset email sent successfully",
                user_id=str(user.id),
                email=request.email,
            )
            return PasswordResetResponse(
                message="If an account with that email exists, a password reset link has been sent.",
                email_sent=True,
            )
        logger.error(
            "Failed to send password reset email",
            user_id=str(user.id),
            email=request.email,
        )
        return PasswordResetResponse(
            message="Failed to send password reset email. Please try again later.",
            email_sent=False,
        )

    except Exception as e:
        logger.error(
            "Password reset request failed with unexpected error",
            email=request.email,
            error=str(e),
            exc_info=True,
        )
        return PasswordResetResponse(
            message="Password reset request failed. Please try again later.",
            email_sent=False,
        )


@router.post("/reset-password", response_model=PasswordResetConfirmResponse)
@rate_limit_password_reset
async def reset_password(
    request: PasswordResetConfirmRequest,
    db: AsyncSession = Depends(get_db),
) -> PasswordResetConfirmResponse:
    """Reset password with token."""
    logger.info("Password reset confirmation attempt")

    try:
        if not email_service or not email_service.is_configured():
            logger.warning(
                "Email service not configured for password reset confirmation",
            )
            return PasswordResetConfirmResponse(
                message="Password reset service temporarily unavailable. Please try again later.",
                password_reset=False,
            )

        # Verify the reset token
        try:
            user_id = await email_service.verify_password_reset_token(db, request.token)
        except Exception:
            logger.warning("Invalid or expired password reset token")
            user_id = None
        if not user_id:
            logger.warning("Invalid or expired password reset token")
            return PasswordResetConfirmResponse(
                message="Invalid or expired password reset token. Please request a new one.",
                password_reset=False,
            )

        # Get user
        user = await crud_user.get_user_by_id(db, user_id)
        if not user:
            logger.warning("User not found for password reset", user_id=user_id)
            return PasswordResetConfirmResponse(
                message="User not found.",
                password_reset=False,
            )

        # Don't allow password reset for OAuth users
        if user.oauth_provider:
            logger.warning(
                "Password reset attempted for OAuth user",
                user_id=str(user.id),
                oauth_provider=user.oauth_provider,
            )
            return PasswordResetConfirmResponse(
                message="Invalid or expired password reset token. Please request a new one.",
                password_reset=False,
            )

        # Reset the password
        success = await crud_user.reset_user_password(db, user_id, request.new_password)
        if not success:
            logger.error("Failed to reset user password", user_id=user_id)
            return PasswordResetConfirmResponse(
                message="Failed to reset password. Please try again later.",
                password_reset=False,
            )

        logger.info("Password reset successful", user_id=str(user.id), email=user.email)
        return PasswordResetConfirmResponse(
            message="Password reset successfully. You can now log in with your new password.",
            password_reset=True,
        )

    except Exception as e:
        logger.error(
            "Password reset confirmation failed with unexpected error",
            error=str(e),
            exc_info=True,
        )
        return PasswordResetConfirmResponse(
            message="Password reset failed. Please try again later.",
            password_reset=False,
        )


@router.post("/change-password", response_model=PasswordChangeResponse)
async def change_password(
    request: Request,
    change_req: PasswordChangeRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PasswordChangeResponse:
    """Change user password."""
    logger.info("Password change attempt", user_id=str(current_user.id))

    def _handle_oauth_user_password_change() -> NoReturn:
        """Handle OAuth user password change error."""
        raise HTTPException(
            status_code=400,
            detail="OAuth users cannot change password",
        )

    def _handle_user_not_found() -> NoReturn:
        """Handle user not found error."""
        raise HTTPException(
            status_code=500,
            detail="User not found. Please try again later.",
        )

    def _handle_incorrect_current_password() -> NoReturn:
        """Handle incorrect current password error."""
        raise HTTPException(status_code=400, detail="Incorrect current password")

    def _handle_password_change_failure() -> NoReturn:
        """Handle password change failure error."""
        raise HTTPException(
            status_code=500,
            detail="Failed to change password. Please try again later.",
        )

    def _handle_general_password_error(exc: Exception) -> NoReturn:
        """Handle general password change error."""
        raise HTTPException(
            status_code=500,
            detail="Password change failed. Please try again later.",
        ) from exc

    try:
        # Don't allow password change for OAuth users
        if current_user.oauth_provider:
            logger.warning(
                "Password change attempted for OAuth user",
                user_id=str(current_user.id),
                oauth_provider=current_user.oauth_provider,
            )
            _handle_oauth_user_password_change()

        # Get the actual user object from database to access hashed_password
        db_user = await crud_user.get_user_by_email(db, current_user.email)
        if not db_user:
            logger.error("User not found in database", user_id=str(current_user.id))
            _handle_user_not_found()

        # Verify the current password
        if not verify_password(
            change_req.current_password,
            str(db_user.hashed_password),
        ):
            logger.warning(
                "Password change failed - incorrect current password",
                user_id=str(current_user.id),
            )
            _handle_incorrect_current_password()

        # Change the password
        success = await crud_user.update_user_password(
            db,
            str(current_user.id),
            change_req.new_password,
        )
        if not success:
            logger.error("Failed to change user password", user_id=str(current_user.id))
            _handle_password_change_failure()

        # Log password change
        await log_password_change(
            db,
            request=request,
            user=db_user,
            change_type="password_change",
        )

        logger.info(
            "Password changed successfully",
            user_id=str(current_user.id),
            email=current_user.email,
        )
        return PasswordChangeResponse(detail="Password updated successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Password change failed with unexpected error",
            user_id=str(current_user.id),
            error=str(e),
            exc_info=True,
        )
        _handle_general_password_error(e)
