from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.api_v1.endpoints.users import get_current_user
from app.core.config import settings
from app.core.logging_config import get_auth_logger
from app.core.security import create_access_token, verify_password
from app.crud import user as crud_user
from app.database.database import get_db
from app.schemas.user import (
    AccountDeletionCancelRequest,
    AccountDeletionCancelResponse,
    AccountDeletionConfirmRequest,
    AccountDeletionConfirmResponse,
    AccountDeletionRequest,
    AccountDeletionResponse,
    AccountDeletionStatusResponse,
    EmailVerificationRequest,
    EmailVerificationResponse,
    OAuthLogin,
    PasswordChangeRequest,
    PasswordChangeResponse,
    PasswordResetConfirmRequest,
    PasswordResetConfirmResponse,
    PasswordResetRequest,
    PasswordResetResponse,
    Token,
    UserCreate,
    UserResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
)

# Import services from the services module
# Import rate limiting decorators
from app.services import (
    email_service,
    oauth_service,
    rate_limit_account_deletion,
    rate_limit_email_verification,
    rate_limit_login,
    rate_limit_oauth,
    rate_limit_password_reset,
    rate_limit_register,
)

router = APIRouter()
logger = get_auth_logger()


@router.post("/register", response_model=UserResponse, status_code=201)
@rate_limit_register
async def register_user(
    user: UserCreate, db: Session = Depends(get_db)
) -> UserResponse:
    logger.info("User registration attempt",
                email=user.email, username=user.username)

    try:
        # Check if user with email already exists
        db_user = crud_user.get_user_by_email_sync(db, email=user.email)
        if db_user:
            logger.warning(
                "Registration failed - email already exists", email=user.email
            )
            raise HTTPException(
                status_code=400,
                detail="Email already registered. Please use a different email or try logging in.",
            )

        # Check if username already exists
        db_user = crud_user.get_user_by_username_sync(
            db, username=user.username)
        if db_user:
            logger.warning(
                "Registration failed - username already taken", username=user.username
            )
            raise HTTPException(
                status_code=400,
                detail="Username already taken. Please choose a different username.",
            )

        # Create new user (not verified initially)
        db_user = crud_user.create_user_sync(db=db, user=user)
        logger.info(
            "User created successfully", user_id=str(db_user.id), email=user.email
        )

        # Send verification email if service is available
        if email_service and email_service.is_configured():
            verification_token = await email_service.create_verification_token(
                db, str(db_user.id)
            )
            if verification_token:
                email_service.send_verification_email(
                    str(user.email), str(user.username), verification_token
                )
                logger.info(
                    "Verification email sent", user_id=str(db_user.id), email=user.email
                )
            else:
                logger.warning(
                    "Failed to create verification token", user_id=str(db_user.id)
                )
        else:
            logger.warning(
                "Email service not configured - skipping verification email")

        return db_user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Registration failed with unexpected error",
            email=user.email,
            username=user.username,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="Registration failed. Please try again later."
        )


@router.post("/login", response_model=Token)
@rate_limit_login
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
) -> Token:
    logger.info("Login attempt", email=form_data.username)

    try:
        # Validate email format
        from app.core.validation import validate_email_format

        is_valid, error_msg = validate_email_format(form_data.username)
        if not is_valid:
            logger.warning(
                "Login failed - invalid email format", email=form_data.username
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format",
            )

        user = crud_user.authenticate_user_sync(
            db, form_data.username, form_data.password
        )
        if not user:
            logger.warning(
                "Login failed - invalid credentials", email=form_data.username
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password. Please check your credentials and try again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user is verified (for non-OAuth users)
        if not user.is_verified and user.hashed_password:
            logger.warning(
                "Login failed - email not verified",
                user_id=str(user.id),
                email=form_data.username,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Please verify your email before logging in. Check your inbox for a verification link.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.email, expires_delta=access_token_expires
        )

        logger.info("Login successful", user_id=str(
            user.id), email=form_data.username)
        return Token(access_token=access_token, token_type="bearer")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Login failed with unexpected error",
            email=form_data.username,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again later.",
        )


@router.post("/oauth/login", response_model=Token)
@rate_limit_oauth
async def oauth_login(oauth_data: OAuthLogin, db: Session = Depends(get_db)) -> Token:
    """Login with OAuth provider (Google or Apple)."""
    logger.info("OAuth login attempt", provider=oauth_data.provider)

    if not oauth_service:
        logger.error("OAuth service not available")
        raise HTTPException(
            status_code=503, detail="OAuth service not available")

    provider = oauth_data.provider.lower()

    if provider not in ["google", "apple"]:
        logger.warning(
            "OAuth login failed - unsupported provider", provider=provider)
        raise HTTPException(
            status_code=400, detail="Unsupported OAuth provider")

    if not oauth_service.is_provider_configured(provider):
        logger.warning(
            "OAuth login failed - provider not configured", provider=provider
        )
        raise HTTPException(
            status_code=400, detail=f"{provider.title()} OAuth not configured"
        )

    try:
        # Verify the OAuth token and get user info
        if provider == "google":
            user_info = await oauth_service.verify_google_token(oauth_data.access_token)
            if not user_info:
                logger.warning(
                    "OAuth login failed - invalid Google token", provider=provider
                )
                raise HTTPException(
                    status_code=400, detail="Invalid Google token")

            oauth_id = user_info.get("sub")
            email = user_info.get("email")
            name = user_info.get("name")

        elif provider == "apple":
            user_info = await oauth_service.verify_apple_token(oauth_data.access_token)
            if not user_info:
                logger.warning(
                    "OAuth login failed - invalid Apple token", provider=provider
                )
                raise HTTPException(
                    status_code=400, detail="Invalid Apple token")

            oauth_id = user_info.get("sub")
            email = user_info.get("email")
            name = user_info.get("name", "")

        if not oauth_id or not email:
            logger.warning(
                "OAuth login failed - invalid user info",
                provider=provider,
                has_oauth_id=bool(oauth_id),
                has_email=bool(email),
            )
            raise HTTPException(
                status_code=400, detail="Invalid OAuth user info")

        logger.info(
            "OAuth token verified successfully",
            provider=provider,
            oauth_id=oauth_id,
            email=email,
        )

        # Check if user already exists
        existing_user = crud_user.get_user_by_oauth_id_sync(
            db, provider, oauth_id)
        if existing_user:
            # User exists, generate token
            access_token_expires = timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
            access_token = create_access_token(
                subject=existing_user.email, expires_delta=access_token_expires
            )
            logger.info(
                "OAuth login successful - existing user",
                user_id=str(existing_user.id),
                provider=provider,
                email=email,
            )
            return Token(access_token=access_token, token_type="bearer")

        # Check if email is already registered with different method
        existing_email_user = crud_user.get_user_by_email_sync(db, email)
        if existing_email_user:
            logger.warning(
                "OAuth login failed - email already registered with different method",
                email=email,
                provider=provider,
            )
            raise HTTPException(
                status_code=400, detail="Email already registered with different method"
            )

        # Create new OAuth user
        username = f"{provider}_{oauth_id[:8]}"  # Generate unique username
        # Ensure username is unique
        counter = 1
        original_username = username
        while crud_user.get_user_by_username_sync(db, username):
            username = f"{original_username}_{counter}"
            counter += 1

        new_user = crud_user.create_oauth_user_sync(
            db=db,
            email=email,
            username=username,
            oauth_provider=provider,
            oauth_id=oauth_id,
            oauth_email=email,
            name=name,
        )

        # Generate token for new user
        access_token_expires = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=new_user.email, expires_delta=access_token_expires
        )
        logger.info(
            "OAuth login successful - new user",
            user_id=str(new_user.id),
            provider=provider,
            email=email,
        )
        return Token(access_token=access_token, token_type="bearer")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "OAuth login failed with unexpected error",
            provider=oauth_data.provider,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=400, detail=f"OAuth login failed: {str(e)}")


@router.post("/resend-verification", response_model=EmailVerificationResponse)
@rate_limit_email_verification
async def resend_verification_email(
    request: EmailVerificationRequest, db: Session = Depends(get_db)
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
    request: VerifyEmailRequest, db: Session = Depends(get_db)
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


@router.get("/oauth/providers")
async def get_oauth_providers() -> dict:
    """Get available OAuth providers."""
    if not oauth_service:
        return {"providers": []}

    providers = []
    if oauth_service.is_provider_configured("google"):
        providers.append("google")
    if oauth_service.is_provider_configured("apple"):
        providers.append("apple")

    return {"providers": providers}


@router.post("/forgot-password", response_model=PasswordResetResponse)
@rate_limit_password_reset
async def forgot_password(
    request: PasswordResetRequest, db: Session = Depends(get_db)
) -> PasswordResetResponse:
    """Request password reset."""
    logger.info("Password reset request", email=request.email)

    try:
        # Check if user exists
        user = crud_user.get_user_by_email_sync(db, email=request.email)
        if not user:
            # Don't reveal if user exists or not for security
            logger.info(
                "Password reset request for non-existent user", email=request.email
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
                "Email service not configured for password reset", email=request.email
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
            str(user.email), str(user.username), reset_token
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
        else:
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
    request: PasswordResetConfirmRequest, db: Session = Depends(get_db)
) -> PasswordResetConfirmResponse:
    """Reset password with token."""
    logger.info("Password reset confirmation attempt")

    try:
        if not email_service or not email_service.is_configured():
            logger.warning(
                "Email service not configured for password reset confirmation"
            )
            return PasswordResetConfirmResponse(
                message="Password reset service temporarily unavailable. Please try again later.",
                password_reset=False,
            )

        # Verify the reset token
        user_id = await email_service.verify_password_reset_token(db, request.token)
        if not user_id:
            logger.warning("Invalid or expired password reset token")
            return PasswordResetConfirmResponse(
                message="Invalid or expired password reset token. Please request a new one.",
                password_reset=False,
            )

        # Get user
        user = crud_user.get_user_by_id_sync(db, user_id)
        if not user:
            logger.warning("User not found for password reset",
                           user_id=user_id)
            return PasswordResetConfirmResponse(
                message="User not found.", password_reset=False
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
        success = crud_user.reset_user_password_sync(
            db, user_id, request.new_password)
        if not success:
            logger.error("Failed to reset user password", user_id=user_id)
            return PasswordResetConfirmResponse(
                message="Failed to reset password. Please try again later.",
                password_reset=False,
            )

        logger.info("Password reset successful",
                    user_id=str(user.id), email=user.email)
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
    request: PasswordChangeRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> PasswordChangeResponse:
    """Change user password."""
    logger.info("Password change attempt", user_id=str(current_user.id))

    try:
        # Don't allow password change for OAuth users
        if current_user.oauth_provider:
            logger.warning(
                "Password change attempted for OAuth user",
                user_id=str(current_user.id),
                oauth_provider=current_user.oauth_provider,
            )
            raise HTTPException(
                status_code=400,
                detail="OAuth users cannot change password"
            )

        # Get the actual user object from database to access hashed_password
        db_user = crud_user.get_user_by_email_sync(db, current_user.email)
        if not db_user:
            logger.error("User not found in database",
                         user_id=str(current_user.id))
            raise HTTPException(
                status_code=500,
                detail="User not found. Please try again later."
            )

        # Verify the current password
        if not verify_password(request.current_password, str(db_user.hashed_password)):
            logger.warning(
                "Password change failed - incorrect current password",
                user_id=str(current_user.id)
            )
            raise HTTPException(
                status_code=400,
                detail="Incorrect current password"
            )

        # Change the password
        success = crud_user.update_user_password_sync(
            db, str(current_user.id), request.new_password)
        if not success:
            logger.error("Failed to change user password",
                         user_id=str(current_user.id))
            raise HTTPException(
                status_code=500,
                detail="Failed to change password. Please try again later."
            )

        logger.info("Password changed successfully", user_id=str(
            current_user.id), email=current_user.email)
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
        raise HTTPException(
            status_code=500,
            detail="Password change failed. Please try again later."
        )


# Account deletion endpoints (GDPR compliance)
@router.post("/request-deletion", response_model=AccountDeletionResponse)
@rate_limit_account_deletion
async def request_account_deletion(
    request: AccountDeletionRequest, db: Session = Depends(get_db)
) -> AccountDeletionResponse:
    """Request account deletion."""
    logger.info("Account deletion request", email=request.email)

    try:
        # Check if user exists
        user = crud_user.get_user_by_email_sync(db, email=request.email)
        if not user:
            # Don't reveal if user exists or not for security
            logger.info(
                "Account deletion request for non-existent user", email=request.email
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
                email=request.email,
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
                email=request.email,
            )
            return AccountDeletionResponse(
                message="If an account with that email exists, a deletion confirmation link has been sent.",
                email_sent=True,
            )

        if not email_service or not email_service.is_configured():
            logger.warning(
                "Email service not configured for account deletion", email=request.email
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
                email=request.email,
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
                email=request.email,
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
            logger.info(
                "Account deletion email sent successfully",
                user_id=str(user.id),
                email=request.email,
            )
            return AccountDeletionResponse(
                message="If an account with that email exists, a deletion confirmation link has been sent.",
                email_sent=True,
            )
        else:
            logger.error(
                "Failed to send account deletion email",
                user_id=str(user.id),
                email=request.email,
            )
            return AccountDeletionResponse(
                message="Failed to send deletion confirmation email. Please try again later.",
                email_sent=False,
            )

    except Exception as e:
        logger.error(
            "Account deletion request failed with unexpected error",
            email=request.email,
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
    request: AccountDeletionConfirmRequest, db: Session = Depends(get_db)
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
        user_id = await email_service.verify_deletion_token(db, request.token)
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
        success = crud_user.confirm_account_deletion_sync(
            db, user_id, deletion_scheduled_for
        )
        if not success:
            logger.error("Failed to confirm account deletion", user_id=user_id)
            return AccountDeletionConfirmResponse(
                message="Failed to confirm account deletion. Please try again later.",
                deletion_confirmed=False,
                deletion_scheduled_for=datetime.utcnow(),
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
    request: AccountDeletionCancelRequest, db: Session = Depends(get_db)
) -> AccountDeletionCancelResponse:
    """Cancel account deletion."""
    logger.info("Account deletion cancellation request", email=request.email)

    try:
        # Check if user exists
        user = crud_user.get_user_by_email_sync(db, email=request.email)
        if not user:
            # Don't reveal if user exists or not for security
            logger.info(
                "Account deletion cancellation for non-existent user",
                email=request.email,
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
                email=request.email,
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
                email=request.email,
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
                email=request.email,
            )
            return AccountDeletionCancelResponse(
                message="Failed to cancel account deletion. Please try again later.",
                deletion_cancelled=False,
            )

        logger.info(
            "Account deletion cancelled successfully",
            user_id=str(user.id),
            email=request.email,
        )
        return AccountDeletionCancelResponse(
            message="Account deletion has been cancelled. Your account is safe.",
            deletion_cancelled=True,
        )

    except Exception as e:
        logger.error(
            "Account deletion cancellation failed with unexpected error",
            email=request.email,
            error=str(e),
            exc_info=True,
        )
        return AccountDeletionCancelResponse(
            message="Account deletion cancellation failed. Please try again later.",
            deletion_cancelled=False,
        )


@router.get("/deletion-status", response_model=AccountDeletionStatusResponse)
async def get_account_deletion_status(
    email: str, db: Session = Depends(get_db)
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

        return AccountDeletionStatusResponse(
            deletion_requested=deletion_requested,
            deletion_confirmed=deletion_confirmed,
            deletion_scheduled_for=user.deletion_scheduled_for
            if user.deletion_scheduled_for
            else None,  # type: ignore
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
