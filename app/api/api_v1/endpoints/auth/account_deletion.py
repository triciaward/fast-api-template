from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging_config import get_auth_logger
from app.crud import user as crud_user
from app.database.database import get_db_sync
from app.schemas.user import (
    AccountDeletionCancelRequest,
    AccountDeletionCancelResponse,
    AccountDeletionConfirmRequest,
    AccountDeletionConfirmResponse,
    AccountDeletionRequest,
    AccountDeletionResponse,
    AccountDeletionStatusResponse,
)
from app.services import email_service, rate_limit_account_deletion
from app.services.audit import log_account_deletion

router = APIRouter()
logger = get_auth_logger()


@router.post("/request-deletion", response_model=AccountDeletionResponse)
@rate_limit_account_deletion
async def request_account_deletion(
    request: Request,
    deletion_request: AccountDeletionRequest,
    db: Session = Depends(get_db_sync),
) -> AccountDeletionResponse:
    """Request account deletion."""
    logger.info("Account deletion request", email=deletion_request.email)

    try:
        # Check if user exists
        user = crud_user.get_user_by_email_sync(
            db, email=deletion_request.email)
        if not user:
            # Don't reveal if user exists or not for security
            logger.info(
                "Account deletion request for non-existent user",
                email=deletion_request.email,
            )
            return AccountDeletionResponse(
                message="If an account with that email exists, a deletion confirmation link has been sent.",
                email_sent=True,
            )

        # Check if user is already deleted
        if user.is_deleted:
            logger.warning(
                "Account deletion requested for already deleted user",
                user_id=str(user.id),
                email=deletion_request.email,
            )
            return AccountDeletionResponse(
                message="If an account with that email exists, a deletion confirmation link has been sent.",
                email_sent=True,
            )

        # Check if deletion is already requested
        if user.deletion_requested_at:
            logger.info(
                "Account deletion already requested",
                user_id=str(user.id),
                email=deletion_request.email,
            )
            return AccountDeletionResponse(
                message="If an account with that email exists, a deletion confirmation link has been sent.",
                email_sent=True,
            )

        if not email_service or not email_service.is_configured():
            logger.warning(
                "Email service not configured for account deletion",
                email=deletion_request.email,
            )
            return AccountDeletionResponse(
                message="Account deletion service temporarily unavailable. Please try again later.",
                email_sent=False,
            )

        # Create deletion token and mark deletion as requested
        deletion_token = await email_service.create_deletion_token(db, str(user.id))
        if not deletion_token:
            logger.error(
                "Failed to create deletion token",
                user_id=str(user.id),
                email=deletion_request.email,
            )
            return AccountDeletionResponse(
                message="Failed to create deletion token. Please try again later.",
                email_sent=False,
            )

        # Mark deletion as requested
        success = crud_user.request_account_deletion_sync(db, str(user.id))
        if not success:
            logger.error(
                "Failed to mark account for deletion",
                user_id=str(user.id),
                email=deletion_request.email,
            )
            return AccountDeletionResponse(
                message="Failed to process deletion request. Please try again later.",
                email_sent=False,
            )

        # Send deletion confirmation email
        email_sent = email_service.send_account_deletion_email(
            str(user.email), str(user.username), deletion_token
        )

        if email_sent:
            # Log account deletion request
            await log_account_deletion(
                db, request, user, deletion_stage="deletion_requested"
            )

            logger.info(
                "Account deletion email sent successfully",
                user_id=str(user.id),
                email=deletion_request.email,
            )
            return AccountDeletionResponse(
                message="If an account with that email exists, a deletion confirmation link has been sent.",
                email_sent=True,
            )
        else:
            logger.error(
                "Failed to send account deletion email",
                user_id=str(user.id),
                email=deletion_request.email,
            )
            return AccountDeletionResponse(
                message="Failed to send deletion confirmation email. Please try again later.",
                email_sent=False,
            )

    except Exception as e:
        logger.error(
            "Account deletion request failed with unexpected error",
            email=deletion_request.email,
            error=str(e),
            exc_info=True,
        )
        return AccountDeletionResponse(
            message="Account deletion request failed. Please try again later.",
            email_sent=False,
        )


@router.post("/confirm-deletion", response_model=AccountDeletionConfirmResponse)
@rate_limit_account_deletion
async def confirm_account_deletion(
    request: Request,
    deletion_request: AccountDeletionConfirmRequest,
    db: Session = Depends(get_db_sync),
) -> AccountDeletionConfirmResponse:
    """Confirm account deletion with token."""
    logger.info("Account deletion confirmation attempt")

    try:
        if not email_service or not email_service.is_configured():
            logger.warning(
                "Email service not configured for account deletion confirmation"
            )
            return AccountDeletionConfirmResponse(
                message="Account deletion service temporarily unavailable. Please try again later.",
                deletion_confirmed=False,
                deletion_scheduled_for=datetime.utcnow(),
            )

        # Verify the deletion token
        user_id = await email_service.verify_deletion_token(db, deletion_request.token)
        if not user_id:
            logger.warning("Invalid or expired deletion token")
            return AccountDeletionConfirmResponse(
                message="Invalid or expired deletion token. Please request a new one.",
                deletion_confirmed=False,
                deletion_scheduled_for=datetime.utcnow(),
            )

        # Get user
        user = crud_user.get_user_by_id_sync(db, user_id)
        if not user:
            logger.warning(
                "User not found for account deletion", user_id=user_id)
            return AccountDeletionConfirmResponse(
                message="User not found.",
                deletion_confirmed=False,
                deletion_scheduled_for=datetime.utcnow(),
            )

        # Check if user is already deleted
        if user.is_deleted:
            logger.warning(
                "Account deletion confirmed for already deleted user",
                user_id=str(user.id),
            )
            return AccountDeletionConfirmResponse(
                message="Account has already been deleted.",
                deletion_confirmed=False,
                deletion_scheduled_for=datetime.utcnow(),
            )

        # Calculate deletion date
        deletion_scheduled_for = datetime.utcnow() + timedelta(
            days=settings.ACCOUNT_DELETION_GRACE_PERIOD_DAYS
        )

        # Confirm deletion
        success = crud_user.confirm_account_deletion_sync(db, user_id)
        if not success:
            logger.error("Failed to confirm account deletion", user_id=user_id)
            return AccountDeletionConfirmResponse(
                message="Failed to confirm account deletion. Please try again later.",
                deletion_confirmed=False,
                deletion_scheduled_for=datetime.utcnow(),
            )

        # Log account deletion confirmation
        await log_account_deletion(
            db, request, user, deletion_stage="deletion_confirmed"
        )

        logger.info(
            "Account deletion confirmed successfully",
            user_id=str(user.id),
            email=user.email,
            deletion_scheduled_for=deletion_scheduled_for,
        )
        return AccountDeletionConfirmResponse(
            message=f"Account deletion confirmed. Your account will be permanently deleted on {deletion_scheduled_for.strftime('%Y-%m-%d %H:%M:%S')} UTC. You can still log in and cancel the deletion during this time.",
            deletion_confirmed=True,
            deletion_scheduled_for=deletion_scheduled_for,
        )

    except Exception as e:
        logger.error(
            "Account deletion confirmation failed with unexpected error",
            error=str(e),
            exc_info=True,
        )
        return AccountDeletionConfirmResponse(
            message="Account deletion confirmation failed. Please try again later.",
            deletion_confirmed=False,
            deletion_scheduled_for=datetime.utcnow(),
        )


@router.post("/cancel-deletion", response_model=AccountDeletionCancelResponse)
@rate_limit_account_deletion
async def cancel_account_deletion(
    request: Request,
    deletion_request: AccountDeletionCancelRequest,
    db: Session = Depends(get_db_sync),
) -> AccountDeletionCancelResponse:
    """Cancel account deletion."""
    logger.info("Account deletion cancellation request",
                email=deletion_request.email)

    try:
        # Check if user exists
        user = crud_user.get_user_by_email_sync(
            db, email=deletion_request.email)
        if not user:
            # Don't reveal if user exists or not for security
            logger.info(
                "Account deletion cancellation for non-existent user",
                email=deletion_request.email,
            )
            return AccountDeletionCancelResponse(
                message="If an account with that email exists and has a pending deletion, it has been cancelled.",
                deletion_cancelled=True,
            )

        # Check if user is already deleted
        if user.is_deleted:
            logger.warning(
                "Account deletion cancellation for already deleted user",
                user_id=str(user.id),
                email=deletion_request.email,
            )
            return AccountDeletionCancelResponse(
                message="If an account with that email exists and has a pending deletion, it has been cancelled.",
                deletion_cancelled=True,
            )

        # Check if deletion is not requested
        if not user.deletion_requested_at:
            logger.info(
                "Account deletion cancellation for user without pending deletion",
                user_id=str(user.id),
                email=deletion_request.email,
            )
            return AccountDeletionCancelResponse(
                message="If an account with that email exists and has a pending deletion, it has been cancelled.",
                deletion_cancelled=True,
            )

        # Cancel deletion
        success = crud_user.cancel_account_deletion_sync(db, str(user.id))
        if not success:
            logger.error(
                "Failed to cancel account deletion",
                user_id=str(user.id),
                email=deletion_request.email,
            )
            return AccountDeletionCancelResponse(
                message="Failed to cancel account deletion. Please try again later.",
                deletion_cancelled=False,
            )

        # Log account deletion cancellation
        await log_account_deletion(
            db, request, user, deletion_stage="deletion_cancelled"
        )

        logger.info(
            "Account deletion cancelled successfully",
            user_id=str(user.id),
            email=deletion_request.email,
        )
        return AccountDeletionCancelResponse(
            message="Account deletion has been cancelled. Your account is safe.",
            deletion_cancelled=True,
        )

    except Exception as e:
        logger.error(
            "Account deletion cancellation failed with unexpected error",
            email=deletion_request.email,
            error=str(e),
            exc_info=True,
        )
        return AccountDeletionCancelResponse(
            message="Account deletion cancellation failed. Please try again later.",
            deletion_cancelled=False,
        )


@router.get("/deletion-status", response_model=AccountDeletionStatusResponse)
async def get_account_deletion_status(
    email: str, db: Session = Depends(get_db_sync)
) -> AccountDeletionStatusResponse:
    """Get account deletion status."""
    logger.info("Account deletion status request", email=email)

    try:
        # Check if user exists
        user = crud_user.get_user_by_email_sync(db, email=email)
        if not user:
            return AccountDeletionStatusResponse(
                deletion_requested=False,
                deletion_confirmed=False,
                deletion_scheduled_for=None,
                can_cancel=False,
                grace_period_days=settings.ACCOUNT_DELETION_GRACE_PERIOD_DAYS,
            )

        # Check if user is already deleted
        if user.is_deleted:
            return AccountDeletionStatusResponse(
                deletion_requested=False,
                deletion_confirmed=False,
                deletion_scheduled_for=None,
                can_cancel=False,
                grace_period_days=settings.ACCOUNT_DELETION_GRACE_PERIOD_DAYS,
            )

        # Check deletion status
        deletion_requested = user.deletion_requested_at is not None
        deletion_confirmed = user.deletion_confirmed_at is not None
        can_cancel = deletion_requested and not user.is_deleted

        # Get deletion scheduled date - handle SQLAlchemy column properly
        scheduled_for = None
        if user.deletion_scheduled_for is not None:
            # Convert SQLAlchemy DateTime to Python datetime
            scheduled_for = datetime.fromisoformat(str(user.deletion_scheduled_for))

        return AccountDeletionStatusResponse(
            deletion_requested=deletion_requested,
            deletion_confirmed=deletion_confirmed,
            deletion_scheduled_for=scheduled_for,
            can_cancel=can_cancel,
            grace_period_days=settings.ACCOUNT_DELETION_GRACE_PERIOD_DAYS,
        )

    except Exception as e:
        logger.error(
            "Account deletion status request failed with unexpected error",
            email=email,
            error=str(e),
            exc_info=True,
        )
        return AccountDeletionStatusResponse(
            deletion_requested=False,
            deletion_confirmed=False,
            deletion_scheduled_for=None,
            can_cancel=False,
            grace_period_days=settings.ACCOUNT_DELETION_GRACE_PERIOD_DAYS,
        )
