import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.api_v1.endpoints.users import get_current_user
from app.core.logging_config import get_auth_logger
from app.core.security import verify_password
from app.crud import user as crud_user
from app.database.database import get_db, get_db_sync
from app.schemas.user import (
    OAuthLogin,
    Token,
    UserCreate,
    UserResponse,
)
from app.services import (
    email_service,
    oauth_service,
    rate_limit_login,
    rate_limit_oauth,
    rate_limit_register,
)
from app.services.audit import log_login_attempt, log_oauth_login

router = APIRouter()
logger = get_auth_logger()


@router.post("/register", response_model=UserResponse, status_code=201)
@rate_limit_register
async def register_user(
    user: UserCreate, db: Session = Depends(get_db_sync)
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

    except IntegrityError as e:
        # Handle database integrity errors (duplicate email/username)
        error_message = str(e)
        if (
            "ix_users_email" in error_message.lower()
            or "email" in error_message.lower()
        ):
            logger.warning(
                "Registration failed - email already exists (integrity error)",
                email=user.email,
            )
            raise HTTPException(
                status_code=400,
                detail="Email already registered. Please use a different email or try logging in.",
            )
        elif (
            "ix_users_username" in error_message.lower()
            or "username" in error_message.lower()
        ):
            logger.warning(
                "Registration failed - username already taken (integrity error)",
                username=user.username,
            )
            raise HTTPException(
                status_code=400,
                detail="Username already taken. Please choose a different username.",
            )
        else:
            logger.error(
                "Registration failed with integrity error",
                email=user.email,
                username=user.username,
                error=error_message,
                exc_info=True,
            )
            raise HTTPException(
                status_code=400,
                detail="Registration failed due to a database constraint violation.",
            )
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
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db_sync),
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
            # Log failed login attempt
            await log_login_attempt(db, request, user=None, success=False)
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
            # Log failed login attempt due to unverified email
            await log_login_attempt(db, request, user=user, success=False)
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

        # Create user session with refresh token
        from app.services.refresh_token import (
            create_user_session,
            set_refresh_token_cookie,
        )

        access_token, refresh_token_value = create_user_session(
            db, user, request)

        # Set refresh token as HttpOnly cookie
        set_refresh_token_cookie(response, refresh_token_value)

        # Log successful login
        await log_login_attempt(db, request, user=user, success=True)

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
async def oauth_login(
    request: Request,
    response: Response,
    oauth_data: OAuthLogin,
    db: Session = Depends(get_db_sync),
) -> Token:
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
            # Create user session with refresh token
            from app.services.refresh_token import (
                create_user_session,
                set_refresh_token_cookie,
            )

            access_token, refresh_token_value = create_user_session(
                db, existing_user, request
            )

            # Set refresh token as HttpOnly cookie
            set_refresh_token_cookie(response, refresh_token_value)

            # Log successful OAuth login for existing user
            await log_oauth_login(db, request, existing_user, provider, success=True)

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

        # Create user session with refresh token
        from app.services.refresh_token import (
            create_user_session,
            set_refresh_token_cookie,
        )

        access_token, refresh_token_value = create_user_session(
            db, new_user, request)

        # Set refresh token as HttpOnly cookie
        set_refresh_token_cookie(response, refresh_token_value)

        # Log successful OAuth login
        await log_oauth_login(db, request, new_user, provider, success=True)

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
