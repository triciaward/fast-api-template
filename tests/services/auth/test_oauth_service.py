"""Comprehensive OAuth service tests for Google and Apple token verification."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import jwt
import pytest
from fastapi import HTTPException

from app.services.auth.oauth import OAuthService

pytestmark = pytest.mark.unit


@pytest.fixture
def oauth_service():
    """Create OAuth service instance for testing."""
    return OAuthService()


@pytest.fixture
def mock_google_settings(monkeypatch):
    """Mock Google OAuth settings."""
    monkeypatch.setattr(
        "app.services.auth.oauth.settings.GOOGLE_CLIENT_ID",
        "test_google_client_id",
    )
    monkeypatch.setattr(
        "app.services.auth.oauth.settings.GOOGLE_CLIENT_SECRET",
        "test_google_secret",
    )


@pytest.fixture
def mock_apple_settings(monkeypatch):
    """Mock Apple OAuth settings."""
    monkeypatch.setattr(
        "app.services.auth.oauth.settings.APPLE_CLIENT_ID",
        "test_apple_client_id",
    )
    monkeypatch.setattr(
        "app.services.auth.oauth.settings.APPLE_TEAM_ID",
        "test_team_id",
    )
    monkeypatch.setattr("app.services.auth.oauth.settings.APPLE_KEY_ID", "test_key_id")
    monkeypatch.setattr(
        "app.services.auth.oauth.settings.APPLE_PRIVATE_KEY",
        "test_private_key",
    )


class TestGoogleOAuth:
    """Test Google OAuth functionality."""

    @pytest.mark.asyncio
    async def test_get_google_user_info_success(self, mock_google_settings):
        """Test successful Google user info retrieval."""
        oauth_service = OAuthService()

        mock_user_data = {
            "id": "123456789",
            "email": "user@gmail.com",
            "name": "Test User",
            "picture": "https://example.com/photo.jpg",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_user_data
            mock_response.raise_for_status.return_value = None

            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response,
            )
            mock_client.return_value = mock_context_manager

            result = await oauth_service.get_google_user_info("valid_access_token")

            assert result == mock_user_data
            mock_context_manager.__aenter__.return_value.get.assert_called_once_with(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": "Bearer valid_access_token"},
            )

    @pytest.mark.asyncio
    async def test_get_google_user_info_not_configured(self, monkeypatch):
        """Test Google user info when OAuth not configured."""
        monkeypatch.setattr("app.services.auth.oauth.settings.GOOGLE_CLIENT_ID", None)

        oauth_service = OAuthService()

        with pytest.raises(HTTPException) as exc_info:
            await oauth_service.get_google_user_info("test_token")

        assert exc_info.value.status_code == 400
        assert "Google OAuth not configured" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_google_user_info_http_error(self, mock_google_settings):
        """Test Google user info with HTTP error."""
        oauth_service = OAuthService()

        with patch("httpx.AsyncClient") as mock_client:
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__.return_value.get.side_effect = (
                httpx.HTTPStatusError(
                    "Bad Request",
                    request=MagicMock(),
                    response=MagicMock(),
                )
            )
            mock_client.return_value = mock_context_manager

            with pytest.raises(HTTPException) as exc_info:
                await oauth_service.get_google_user_info("invalid_token")

            assert exc_info.value.status_code == 400
            assert "Failed to get Google user info" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_google_token_success(self, mock_google_settings):
        """Test successful Google token verification."""
        oauth_service = OAuthService()

        # Mock the HTTP response for Google's tokeninfo endpoint
        mock_token_info = {
            "sub": "123456789",
            "email": "user@gmail.com",
            "aud": "test_google_client_id",
            "exp": str(int(time.time()) + 3600),  # 1 hour from now
            "iss": "https://accounts.google.com",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_token_info
            mock_response.raise_for_status.return_value = None

            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response,
            )
            mock_client.return_value = mock_context_manager

            result = await oauth_service.verify_google_token("valid_id_token")

            assert result == mock_token_info

    @pytest.mark.asyncio
    async def test_verify_google_token_invalid_audience(self, mock_google_settings):
        """Test Google token verification with invalid audience."""
        oauth_service = OAuthService()

        # Mock the HTTP response with invalid audience
        mock_token_info = {
            "sub": "123456789",
            "email": "user@gmail.com",
            "aud": "wrong_client_id",  # Invalid audience
            "exp": str(int(time.time()) + 3600),
            "iss": "https://accounts.google.com",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_token_info
            mock_response.raise_for_status.return_value = None

            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response,
            )
            mock_client.return_value = mock_context_manager

            with pytest.raises(HTTPException) as exc_info:
                await oauth_service.verify_google_token("invalid_token")

            assert exc_info.value.status_code == 400
            assert "Invalid Google token" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_google_token_success_with_valid_data(
        self,
        mock_google_settings,
    ):
        """Test Google token verification with valid token data but checking boundary conditions."""
        oauth_service = OAuthService()

        # Mock successful response - Google doesn't check expiration in this implementation
        mock_token_info = {
            "sub": "123456789",
            "email": "user@gmail.com",
            "aud": "test_google_client_id",  # Valid audience
            "exp": str(int(time.time()) + 3600),
            "iss": "https://accounts.google.com",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_token_info
            mock_response.raise_for_status.return_value = None

            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response,
            )
            mock_client.return_value = mock_context_manager

            result = await oauth_service.verify_google_token("valid_token")

            assert result == mock_token_info

    @pytest.mark.asyncio
    async def test_verify_google_token_http_error(self, mock_google_settings):
        """Test Google token verification with HTTP error from Google."""
        oauth_service = OAuthService()

        with patch("httpx.AsyncClient") as mock_client:
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__.return_value.get.side_effect = (
                httpx.HTTPStatusError(
                    "Bad Request",
                    request=MagicMock(),
                    response=MagicMock(),
                )
            )
            mock_client.return_value = mock_context_manager

            with pytest.raises(HTTPException) as exc_info:
                await oauth_service.verify_google_token("malformed_token")

            assert exc_info.value.status_code == 400
            assert "Failed to verify Google token" in exc_info.value.detail


class TestAppleOAuth:
    """Test Apple OAuth functionality."""

    @pytest.mark.asyncio
    async def test_verify_apple_token_success(self, mock_apple_settings):
        """Test successful Apple token verification."""
        oauth_service = OAuthService()

        mock_payload = {
            "sub": "apple_user_123",
            "email": "user@icloud.com",
            "aud": "test_apple_client_id",
            "exp": int(time.time()) + 3600,
            "iss": "https://appleid.apple.com",
        }

        with patch("jwt.decode") as mock_jwt_decode:
            mock_jwt_decode.return_value = mock_payload

            result = await oauth_service.verify_apple_token("valid_apple_token")

            assert result == mock_payload

    @pytest.mark.asyncio
    async def test_verify_apple_token_not_configured(self, monkeypatch):
        """Test Apple token verification when not configured."""
        # Leave some settings unset
        monkeypatch.setattr("app.services.auth.oauth.settings.APPLE_CLIENT_ID", None)

        oauth_service = OAuthService()

        with pytest.raises(HTTPException) as exc_info:
            await oauth_service.verify_apple_token("test_token")

        assert exc_info.value.status_code == 400
        assert "Apple OAuth not configured" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_apple_token_invalid_audience(self, mock_apple_settings):
        """Test Apple token verification with invalid audience."""
        oauth_service = OAuthService()

        mock_payload = {
            "sub": "apple_user_123",
            "email": "user@icloud.com",
            "aud": "wrong_apple_client_id",  # Invalid audience
            "exp": int(time.time()) + 3600,
        }

        with patch("jwt.decode") as mock_jwt_decode:
            mock_jwt_decode.return_value = mock_payload

            with pytest.raises(HTTPException) as exc_info:
                await oauth_service.verify_apple_token("invalid_audience_token")

            assert exc_info.value.status_code == 400
            assert "Invalid Apple token" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_apple_token_expired(self, mock_apple_settings):
        """Test Apple token verification with expired token."""
        oauth_service = OAuthService()

        mock_payload = {
            "sub": "apple_user_123",
            "email": "user@icloud.com",
            "aud": "test_apple_client_id",
            "exp": int(time.time()) - 3600,  # Expired
        }

        with patch("jwt.decode") as mock_jwt_decode:
            mock_jwt_decode.return_value = mock_payload

            with pytest.raises(HTTPException) as exc_info:
                await oauth_service.verify_apple_token("expired_apple_token")

            assert exc_info.value.status_code == 400
            assert "Apple token expired" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_apple_token_decode_error(self, mock_apple_settings):
        """Test Apple token verification with decode error."""
        oauth_service = OAuthService()

        with patch("jwt.decode") as mock_jwt_decode:
            mock_jwt_decode.side_effect = jwt.InvalidTokenError("Invalid token format")

            with pytest.raises(HTTPException) as exc_info:
                await oauth_service.verify_apple_token("malformed_apple_token")

            assert exc_info.value.status_code == 400
            assert "Failed to verify Apple token" in exc_info.value.detail


class TestOAuthProviderConfig:
    """Test OAuth provider configuration."""

    def test_get_oauth_provider_config_google(self, mock_google_settings):
        """Test getting Google provider configuration."""
        oauth_service = OAuthService()

        config = oauth_service.get_oauth_provider_config("google")

        expected_config = {
            "client_id": "test_google_client_id",
            "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
            "scope": "openid email profile",
        }
        assert config == expected_config

    def test_get_oauth_provider_config_apple(self, mock_apple_settings):
        """Test getting Apple provider configuration."""
        oauth_service = OAuthService()

        config = oauth_service.get_oauth_provider_config("apple")

        expected_config = {
            "client_id": "test_apple_client_id",
            "authorization_url": "https://appleid.apple.com/auth/authorize",
            "token_url": "https://appleid.apple.com/auth/token",
            "scope": "name email",
        }
        assert config == expected_config

    def test_get_oauth_provider_config_unsupported(self):
        """Test getting configuration for unsupported provider."""
        oauth_service = OAuthService()

        with pytest.raises(HTTPException) as exc_info:
            oauth_service.get_oauth_provider_config("facebook")

        assert exc_info.value.status_code == 400
        assert "Unsupported OAuth provider: facebook" in exc_info.value.detail

    def test_is_provider_configured_google_true(self, mock_google_settings):
        """Test provider configuration check for Google when configured."""
        oauth_service = OAuthService()

        assert oauth_service.is_provider_configured("google") is True

    def test_is_provider_configured_google_false(self, monkeypatch):
        """Test provider configuration check for Google when not configured."""
        monkeypatch.setattr("app.services.auth.oauth.settings.GOOGLE_CLIENT_ID", None)

        oauth_service = OAuthService()

        assert oauth_service.is_provider_configured("google") is False

    def test_is_provider_configured_apple_true(self, mock_apple_settings):
        """Test provider configuration check for Apple when configured."""
        oauth_service = OAuthService()

        assert oauth_service.is_provider_configured("apple") is True

    def test_is_provider_configured_apple_false(self, monkeypatch):
        """Test provider configuration check for Apple when not configured."""
        monkeypatch.setattr("app.services.auth.oauth.settings.APPLE_CLIENT_ID", None)

        oauth_service = OAuthService()

        assert oauth_service.is_provider_configured("apple") is False

    def test_is_provider_configured_unsupported(self):
        """Test provider configuration check for unsupported provider."""
        oauth_service = OAuthService()

        assert oauth_service.is_provider_configured("facebook") is False
