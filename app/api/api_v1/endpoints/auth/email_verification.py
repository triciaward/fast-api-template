from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging_config import get_auth_logger
from app.crud import user as crud_user
from app.database.database import get_db, get_db_sync
from app.schemas.user import (
    EmailVerificationRequest,
    EmailVerificationResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
)
from app.services import email_service, rate_limit_email_verification

router = APIRouter()
logger = get_auth_logger()


@router.post("/resend-verification", response_model=EmailVerificationResponse)
@rate_limit_email_verification
async def resend_verification_email(
    request: EmailVerificationRequest, db: Session = Depends(get_db_sync)
) -> EmailVerificationResponse:
    """Resend email verification."""
    user = crud_user.get_user_by_email_sync(db, email=request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        return EmailVerificationResponse(
            message="User is already verified", email_sent=False
        )

    if not email_service or not email_service.is_configured():
        return EmailVerificationResponse(
            message="Email service not configured", email_sent=False
        )

    # Create new verification token
    verification_token = await email_service.create_verification_token(db, str(user.id))
    if not verification_token:
        return EmailVerificationResponse(
            message="Failed to create verification token", email_sent=False
        )

    # Send verification email
    email_sent = email_service.send_verification_email(
        str(user.email), str(user.username), verification_token
    )

    if email_sent:
        return EmailVerificationResponse(
            message="Verification email sent successfully", email_sent=True
        )
    else:
        return EmailVerificationResponse(
            message="Failed to send verification email", email_sent=False
        )


@router.post("/verify-email", response_model=VerifyEmailResponse)
@rate_limit_email_verification
async def verify_email(
    request: VerifyEmailRequest, db: Session = Depends(get_db_sync)
) -> VerifyEmailResponse:
    """Verify email with token."""
    if not email_service or not email_service.is_configured():
        return VerifyEmailResponse(
            message="Email service not configured", verified=False
        )

    # Verify the token
    user_id = await email_service.verify_token(db, request.token)
    if not user_id:
        return VerifyEmailResponse(
            message="Invalid or expired verification token", verified=False
        )

    # Get user and mark as verified
    user = crud_user.get_user_by_id_sync(db, user_id)
    if not user:
        return VerifyEmailResponse(message="User not found", verified=False)

    if user.is_verified:
        return VerifyEmailResponse(message="User is already verified", verified=True)

    # Update user verification status
    success = crud_user.verify_user_sync(db, user_id)
    if not success:
        return VerifyEmailResponse(message="Failed to verify user", verified=False)

    return VerifyEmailResponse(message="Email verified successfully", verified=True)
