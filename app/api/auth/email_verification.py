from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.logging_config import get_auth_logger
from app.crud.auth import user as crud_user
from app.database.database import get_db
from app.schemas.auth.user import (
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
    request: EmailVerificationRequest,
    db: AsyncSession = Depends(get_db),
) -> EmailVerificationResponse:
    """Resend email verification."""
    user = await crud_user.get_user_by_email(db, email=request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        return EmailVerificationResponse(
            message="User is already verified",
            email_sent=False,
        )

    if not email_service or not email_service.is_configured():
        return EmailVerificationResponse(
            message="Email service not configured",
            email_sent=False,
        )

    # Create new verification token
    verification_token = await email_service.create_verification_token(db, str(user.id))
    if not verification_token:
        return EmailVerificationResponse(
            message="Failed to create verification token",
            email_sent=False,
        )

    # Send verification email
    email_sent = email_service.send_verification_email(
        str(user.email),
        str(user.username),
        verification_token,
    )

    if email_sent:
        return EmailVerificationResponse(
            message="Verification email sent successfully",
            email_sent=True,
        )
    return EmailVerificationResponse(
        message="Failed to send verification email",
        email_sent=False,
    )


@router.post("/verify-email", response_model=VerifyEmailResponse)
@rate_limit_email_verification
async def verify_email(
    request: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
) -> VerifyEmailResponse:
    """Verify email with token."""
    if not email_service or not email_service.is_configured():
        return VerifyEmailResponse(
            message="Email service not configured",
            verified=False,
        )

    # Verify the token
    try:
        user_id = await email_service.verify_token(db, request.token)
    except Exception:
        # Treat verification errors as invalid tokens rather than surfacing exceptions
        user_id = None
    if not user_id:
        return VerifyEmailResponse(
            message="Invalid or expired verification token",
            verified=False,
        )

    # Get user and mark as verified
    user = await crud_user.get_user_by_id(db, user_id)
    if not user:
        return VerifyEmailResponse(message="User not found", verified=False)

    if user.is_verified:
        return VerifyEmailResponse(message="User is already verified", verified=True)

    # Update user verification status
    success = await crud_user.verify_user(db, user_id)
    if not success:
        return VerifyEmailResponse(message="Failed to verify user", verified=False)

    return VerifyEmailResponse(message="Email verified successfully", verified=True)
