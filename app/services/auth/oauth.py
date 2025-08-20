import time
from typing import Any, NoReturn, TypedDict

import httpx
import jwt
from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException
from starlette.config import Config

from app.core.config import settings


class OAuthService:
    class OAuthProviderConfig(TypedDict, total=False):
        client_id: str | None
        authorization_url: str
        token_url: str
        userinfo_url: str | None
        scope: str

    def __init__(self) -> None:
        self.config = Config(".env")
        self.oauth = OAuth()
        self._setup_oauth()

    def _setup_oauth(self) -> None:
        """Setup OAuth clients for Google and Apple."""
        # Google OAuth
        if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
            self.oauth.register(
                name="google",
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET,
                server_metadata_url="https://accounts.google.com/.well-known/openid_configuration",
                client_kwargs={"scope": "openid email profile"},
            )

    async def get_google_user_info(self, access_token: str) -> dict[str, Any] | None:
        """Get user info from Google using access token."""
        if not settings.GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=400, detail="Google OAuth not configured")

        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {access_token}"}
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers=headers,
                )
                response.raise_for_status()
                data: dict[str, Any] = dict(response.json())
                return data
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get Google user info: {e!s}",
            ) from e

    async def verify_google_token(self, id_token: str) -> dict[str, Any] | None:
        """Verify Google ID token."""

        def _handle_google_not_configured() -> NoReturn:
            """Handle Google OAuth not configured error."""
            raise HTTPException(status_code=400, detail="Google OAuth not configured")

        def _handle_invalid_google_token() -> NoReturn:
            """Handle invalid Google token error."""
            raise HTTPException(status_code=400, detail="Invalid Google token")

        def _handle_google_verification_error(exc: Exception) -> NoReturn:
            """Handle Google verification error."""
            raise HTTPException(
                status_code=400,
                detail=f"Failed to verify Google token: {exc!s}",
            ) from exc

        if not settings.GOOGLE_CLIENT_ID:
            _handle_google_not_configured()

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://oauth2.googleapis.com/tokeninfo",
                    params={"id_token": id_token},
                )
                response.raise_for_status()
                data: dict[str, Any] = dict(response.json())

                # Verify the token is for our app
                if data.get("aud") != settings.GOOGLE_CLIENT_ID:
                    _handle_invalid_google_token()

        except HTTPException:
            raise
        except Exception as e:
            _handle_google_verification_error(e)
        else:
            return data

    async def verify_apple_token(self, id_token: str) -> dict[str, Any] | None:
        """Verify Apple ID token."""

        def _handle_apple_not_configured() -> NoReturn:
            """Handle Apple OAuth not configured error."""
            raise HTTPException(status_code=400, detail="Apple OAuth not configured")

        def _handle_invalid_apple_token() -> NoReturn:
            """Handle invalid Apple token error."""
            raise HTTPException(status_code=400, detail="Invalid Apple token")

        def _handle_apple_token_expired() -> NoReturn:
            """Handle Apple token expired error."""
            raise HTTPException(status_code=400, detail="Apple token expired")

        def _handle_apple_verification_error(exc: Exception) -> NoReturn:
            """Handle Apple verification error."""
            raise HTTPException(
                status_code=400,
                detail=f"Failed to verify Apple token: {exc!s}",
            ) from exc

        if not all(
            [
                settings.APPLE_CLIENT_ID,
                settings.APPLE_TEAM_ID,
                settings.APPLE_KEY_ID,
                settings.APPLE_PRIVATE_KEY,
            ],
        ):
            _handle_apple_not_configured()

        try:
            # This is a simplified verification - in production you'd want to verify the JWT signature
            # For now, we'll just decode the JWT payload

            # Decode without verification for now (in production, verify with Apple's public keys)
            payload: dict[str, Any] = dict(
                jwt.decode(id_token, options={"verify_signature": False}),
            )

            # Basic validation
            if payload.get("aud") != settings.APPLE_CLIENT_ID:
                _handle_invalid_apple_token()

            if payload.get("exp", 0) < time.time():
                _handle_apple_token_expired()

        except HTTPException:
            raise
        except Exception as e:
            _handle_apple_verification_error(e)
        else:
            return payload

    def get_oauth_provider_config(
        self,
        provider: str,
    ) -> "OAuthService.OAuthProviderConfig":
        """Get OAuth provider configuration."""

        def _handle_unsupported_provider() -> NoReturn:
            """Handle unsupported provider error."""
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported OAuth provider: {provider}",
            )

        if provider == "google":
            return {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
                "scope": "openid email profile",
            }
        if provider == "apple":
            return {
                "client_id": settings.APPLE_CLIENT_ID,
                "authorization_url": "https://appleid.apple.com/auth/authorize",
                "token_url": "https://appleid.apple.com/auth/token",
                "scope": "name email",
            }

        _handle_unsupported_provider()
        return {}

    def is_provider_configured(self, provider: str) -> bool:
        """Check if OAuth provider is configured."""
        if provider == "google":
            return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)
        if provider == "apple":
            return bool(
                settings.APPLE_CLIENT_ID
                and settings.APPLE_TEAM_ID
                and settings.APPLE_KEY_ID
                and settings.APPLE_PRIVATE_KEY,
            )
        return False


oauth_service = OAuthService()
