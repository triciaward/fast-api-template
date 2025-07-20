from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging_config import get_auth_logger
from app.core.security import create_access_token
from app.crud import user as crud_user
from app.database.database import get_db
from app.schemas.user import (
    EmailVerificationRequest,
    EmailVerificationResponse,
    OAuthLogin,
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
    rate_limit_email_verification,
    rate_limit_login,
    rate_limit_oauth,
    rate_limit_register,
)

router = APIRouter()
logger = get_auth_logger()


@router.post("/register", response_model=UserResponse, status_code=201)
@rate_limit_register
async def register_user(
    user: UserCreate, db: Session = Depends(get_db)
) -> UserResponse:
    logger.info("User registration attempt", email=user.email, username=user.username)

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
        db_user = crud_user.get_user_by_username_sync(db, username=user.username)
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
            logger.warning("Email service not configured - skipping verification email")

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

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.email, expires_delta=access_token_expires
        )

        logger.info("Login successful", user_id=str(user.id), email=form_data.username)
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
        raise HTTPException(status_code=503, detail="OAuth service not available")

    provider = oauth_data.provider.lower()

    if provider not in ["google", "apple"]:
        logger.warning("OAuth login failed - unsupported provider", provider=provider)
        raise HTTPException(status_code=400, detail="Unsupported OAuth provider")

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
                raise HTTPException(status_code=400, detail="Invalid Google token")

            oauth_id = user_info.get("sub")
            email = user_info.get("email")
            name = user_info.get("name")

        elif provider == "apple":
            user_info = await oauth_service.verify_apple_token(oauth_data.access_token)
            if not user_info:
                logger.warning(
                    "OAuth login failed - invalid Apple token", provider=provider
                )
                raise HTTPException(status_code=400, detail="Invalid Apple token")

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
            raise HTTPException(status_code=400, detail="Invalid OAuth user info")

        logger.info(
            "OAuth token verified successfully",
            provider=provider,
            oauth_id=oauth_id,
            email=email,
        )

        # Check if user already exists
        existing_user = crud_user.get_user_by_oauth_id_sync(db, provider, oauth_id)
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
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
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
        raise HTTPException(status_code=400, detail=f"OAuth login failed: {str(e)}")


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
