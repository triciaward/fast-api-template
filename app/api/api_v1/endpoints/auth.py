from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
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

# Initialize services as None - will be set if available
email_service = None
oauth_service = None

# Try to import optional services
try:
    from app.services.email import email_service as _email_service
    email_service = _email_service
except (ImportError, ModuleNotFoundError):
    pass

try:
    from app.services.oauth import oauth_service as _oauth_service
    oauth_service = _oauth_service
except (ImportError, ModuleNotFoundError):
    pass

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register_user(
    user: UserCreate, db: Session = Depends(get_db)
) -> UserResponse:
    # Check if user with email already exists
    db_user = crud_user.get_user_by_email_sync(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check if username already exists
    db_user = crud_user.get_user_by_username_sync(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    # Create new user (not verified initially)
    db_user = crud_user.create_user_sync(db=db, user=user)

    # Send verification email if service is available
    if email_service and email_service.is_configured():
        verification_token = await email_service.create_verification_token(
            db, str(db_user.id)
        )
        if verification_token:
            email_service.send_verification_email(
                str(user.email), str(user.username), verification_token
            )

    return db_user


@router.post("/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
) -> Token:
    user = crud_user.authenticate_user_sync(
        db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is verified (for non-OAuth users)
    if not user.is_verified and user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please verify your email before logging in",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.email, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@router.post("/oauth/login", response_model=Token)
async def oauth_login(oauth_data: OAuthLogin, db: Session = Depends(get_db)) -> Token:
    """Login with OAuth provider (Google or Apple)."""
    if not oauth_service:
        raise HTTPException(
            status_code=503, detail="OAuth service not available")

    provider = oauth_data.provider.lower()

    if provider not in ["google", "apple"]:
        raise HTTPException(
            status_code=400, detail="Unsupported OAuth provider")

    if not oauth_service.is_provider_configured(provider):
        raise HTTPException(
            status_code=400, detail=f"{provider.title()} OAuth not configured"
        )

    try:
        # Verify the OAuth token and get user info
        if provider == "google":
            user_info = await oauth_service.verify_google_token(oauth_data.access_token)
            if not user_info:
                raise HTTPException(
                    status_code=400, detail="Invalid Google token")

            oauth_id = user_info.get("sub")
            email = user_info.get("email")
            name = user_info.get("name")

        elif provider == "apple":
            user_info = await oauth_service.verify_apple_token(oauth_data.access_token)
            if not user_info:
                raise HTTPException(
                    status_code=400, detail="Invalid Apple token")

            oauth_id = user_info.get("sub")
            email = user_info.get("email")
            name = user_info.get("name", "")

        if not oauth_id or not email:
            raise HTTPException(
                status_code=400, detail="Invalid OAuth user info")

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
            return Token(access_token=access_token, token_type="bearer")

        # Check if email is already registered with different method
        existing_email_user = crud_user.get_user_by_email_sync(db, email)
        if existing_email_user:
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
        return Token(access_token=access_token, token_type="bearer")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"OAuth login failed: {str(e)}")


@router.post("/resend-verification", response_model=EmailVerificationResponse)
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
async def verify_email(
    request: VerifyEmailRequest, db: Session = Depends(get_db)
) -> VerifyEmailResponse:
    """Verify email with token."""
    if not email_service:
        return VerifyEmailResponse(
            message="Email service not available", verified=False
        )

    verified = await email_service.verify_token(db, request.token)

    if verified:
        return VerifyEmailResponse(message="Email verified successfully", verified=True)
    else:
        return VerifyEmailResponse(
            message="Invalid or expired verification token", verified=False
        )


@router.get("/oauth/providers")
async def get_oauth_providers() -> dict:
    """Get available OAuth providers."""
    if not oauth_service:
        return {"providers": {}}

    providers = {}

    if oauth_service.is_provider_configured("google"):
        providers["google"] = oauth_service.get_oauth_provider_config("google")

    if oauth_service.is_provider_configured("apple"):
        providers["apple"] = oauth_service.get_oauth_provider_config("apple")

    return {"providers": providers}
