"""
Tests for OAuth service.

This module tests the OAuth service functionality including Google and Apple token verification, user info retrieval, and provider configuration.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import time
# Import jwt only when needed to avoid import issues
# import jwt

from fastapi import HTTPException

from app.services.oauth import OAuthService


class TestOAuthServiceInitialization:
    """Test OAuth service initialization and setup."""

    @patch("app.services.oauth.settings")
    @patch("app.services.oauth.OAuth")
    @patch("app.services.oauth.Config")
    def test_oauth_service_initialization(self, mock_config, mock_oauth, mock_settings):
        """Test OAuth service initialization."""
        # Mock settings
        mock_settings.GOOGLE_CLIENT_ID = "google_client_id"
        mock_settings.GOOGLE_CLIENT_SECRET = "google_client_secret"

        # Mock OAuth and Config
        mock_oauth_instance = MagicMock()
        mock_oauth.return_value = mock_oauth_instance
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance

        # Test initialization
        oauth_service = OAuthService()

        # Verify initialization
        assert oauth_service.config == mock_config_instance
        assert oauth_service.oauth == mock_oauth_instance
        mock_oauth_instance.register.assert_called_once()

    @patch("app.services.oauth.settings")
    @patch("app.services.oauth.OAuth")
    @patch("app.services.oauth.Config")
    def test_oauth_service_initialization_no_google_config(self, mock_config, mock_oauth, mock_settings):
        """Test OAuth service initialization without Google configuration."""
        # Mock settings - no Google config
        mock_settings.GOOGLE_CLIENT_ID = None
        mock_settings.GOOGLE_CLIENT_SECRET = None

        # Mock OAuth and Config
        mock_oauth_instance = MagicMock()
        mock_oauth.return_value = mock_oauth_instance
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance

        # Test initialization
        oauth_service = OAuthService()

        # Verify initialization without Google registration
        assert oauth_service.config == mock_config_instance
        assert oauth_service.oauth == mock_oauth_instance
        mock_oauth_instance.register.assert_not_called()


class TestGoogleOAuth:
    """Test Google OAuth functionality."""

    @patch("app.services.oauth.settings")
    @patch("app.services.oauth.httpx.AsyncClient")
    async def test_get_google_user_info_success(self, mock_client, mock_settings):
        """Test successful Google user info retrieval."""
        # Mock settings
        mock_settings.GOOGLE_CLIENT_ID = "google_client_id"

        # Mock HTTP client
        mock_client_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "google_user_id",
            "email": "user@gmail.com",
            "name": "Test User",
            "picture": "https://example.com/avatar.jpg"
        }
        mock_response.raise_for_status.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # Test user info retrieval
        oauth_service = OAuthService()
        result = await oauth_service.get_google_user_info("valid_access_token")

        # Verify result
        assert result["id"] == "google_user_id"
        assert result["email"] == "user@gmail.com"
        assert result["name"] == "Test User"
        assert result["picture"] == "https://example.com/avatar.jpg"

        # Verify HTTP call
        mock_client_instance.get.assert_called_once_with(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": "Bearer valid_access_token"}
        )

    @patch("app.services.oauth.settings")
    async def test_get_google_user_info_not_configured(self, mock_settings):
        """Test Google user info retrieval when not configured."""
        # Mock settings - no Google config
        mock_settings.GOOGLE_CLIENT_ID = None

        # Test user info retrieval
        oauth_service = OAuthService()

        with pytest.raises(HTTPException) as exc_info:
            await oauth_service.get_google_user_info("valid_access_token")

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Google OAuth not configured"

    @patch("app.services.oauth.settings")
    @patch("app.services.oauth.httpx.AsyncClient")
    async def test_get_google_user_info_http_error(self, mock_client, mock_settings):
        """Test Google user info retrieval with HTTP error."""
        # Mock settings
        mock_settings.GOOGLE_CLIENT_ID = "google_client_id"

        # Mock HTTP client with error
        mock_client_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # Test user info retrieval
        oauth_service = OAuthService()

        with pytest.raises(HTTPException) as exc_info:
            await oauth_service.get_google_user_info("valid_access_token")

        assert exc_info.value.status_code == 400
        assert "Failed to get Google user info" in exc_info.value.detail

    @patch("app.services.oauth.settings")
    @patch("app.services.oauth.httpx.AsyncClient")
    async def test_verify_google_token_success(self, mock_client, mock_settings):
        """Test successful Google token verification."""
        # Mock settings
        mock_settings.GOOGLE_CLIENT_ID = "google_client_id"

        # Mock HTTP client
        mock_client_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "aud": "google_client_id",
            "sub": "google_user_id",
            "email": "user@gmail.com",
            "exp": int(time.time()) + 3600  # Valid expiration
        }
        mock_response.raise_for_status.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # Test token verification
        oauth_service = OAuthService()
        result = await oauth_service.verify_google_token("valid_id_token")

        # Verify result
        assert result["aud"] == "google_client_id"
        assert result["sub"] == "google_user_id"
        assert result["email"] == "user@gmail.com"

        # Verify HTTP call
        mock_client_instance.get.assert_called_once_with(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": "valid_id_token"}
        )

    @patch("app.services.oauth.settings")
    async def test_verify_google_token_not_configured(self, mock_settings):
        """Test Google token verification when not configured."""
        # Mock settings - no Google config
        mock_settings.GOOGLE_CLIENT_ID = None

        # Test token verification
        oauth_service = OAuthService()

        with pytest.raises(HTTPException) as exc_info:
            await oauth_service.verify_google_token("valid_id_token")

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Google OAuth not configured"

    @patch("app.services.oauth.settings")
    @patch("app.services.oauth.httpx.AsyncClient")
    async def test_verify_google_token_invalid_audience(self, mock_client, mock_settings):
        """Test Google token verification with invalid audience."""
        # Mock settings
        mock_settings.GOOGLE_CLIENT_ID = "google_client_id"

        # Mock HTTP client
        mock_client_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "aud": "different_client_id",  # Wrong audience
            "sub": "google_user_id",
            "email": "user@gmail.com"
        }
        mock_response.raise_for_status.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # Test token verification
        oauth_service = OAuthService()

        with pytest.raises(HTTPException) as exc_info:
            await oauth_service.verify_google_token("valid_id_token")

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Invalid Google token"

    @patch("app.services.oauth.settings")
    @patch("app.services.oauth.httpx.AsyncClient")
    async def test_verify_google_token_http_error(self, mock_client, mock_settings):
        """Test Google token verification with HTTP error."""
        # Mock settings
        mock_settings.GOOGLE_CLIENT_ID = "google_client_id"

        # Mock HTTP client with error
        mock_client_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # Test token verification
        oauth_service = OAuthService()

        with pytest.raises(HTTPException) as exc_info:
            await oauth_service.verify_google_token("valid_id_token")

        assert exc_info.value.status_code == 400
        assert "Failed to verify Google token" in exc_info.value.detail


class TestAppleOAuth:
    """Test Apple OAuth functionality."""

    @patch("app.services.oauth.settings")
    @patch("app.services.oauth.jwt.decode")
    async def test_verify_apple_token_success(self, mock_jwt_decode, mock_settings):
        """Test successful Apple token verification."""
        # Mock settings
        mock_settings.APPLE_CLIENT_ID = "apple_client_id"
        mock_settings.APPLE_TEAM_ID = "apple_team_id"
        mock_settings.APPLE_KEY_ID = "apple_key_id"
        mock_settings.APPLE_PRIVATE_KEY = "apple_private_key"

        # Mock JWT decode
        mock_jwt_decode.return_value = {
            "aud": "apple_client_id",
            "sub": "apple_user_id",
            "email": "user@example.com",
            "exp": int(time.time()) + 3600  # Valid expiration
        }

        # Test token verification
        oauth_service = OAuthService()
        result = await oauth_service.verify_apple_token("valid_id_token")

        # Verify result
        assert result["aud"] == "apple_client_id"
        assert result["sub"] == "apple_user_id"
        assert result["email"] == "user@example.com"

        # Verify JWT decode call
        mock_jwt_decode.assert_called_once_with(
            "valid_id_token", 
            options={"verify_signature": False}
        )

    @patch("app.services.oauth.settings")
    async def test_verify_apple_token_not_configured(self, mock_settings):
        """Test Apple token verification when not configured."""
        # Mock settings - missing Apple config
        mock_settings.APPLE_CLIENT_ID = None
        mock_settings.APPLE_TEAM_ID = "apple_team_id"
        mock_settings.APPLE_KEY_ID = "apple_key_id"
        mock_settings.APPLE_PRIVATE_KEY = "apple_private_key"

        # Test token verification
        oauth_service = OAuthService()

        with pytest.raises(HTTPException) as exc_info:
            await oauth_service.verify_apple_token("valid_id_token")

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Apple OAuth not configured"

    @patch("app.services.oauth.settings")
    @patch("app.services.oauth.jwt.decode")
    async def test_verify_apple_token_invalid_audience(self, mock_jwt_decode, mock_settings):
        """Test Apple token verification with invalid audience."""
        # Mock settings
        mock_settings.APPLE_CLIENT_ID = "apple_client_id"
        mock_settings.APPLE_TEAM_ID = "apple_team_id"
        mock_settings.APPLE_KEY_ID = "apple_key_id"
        mock_settings.APPLE_PRIVATE_KEY = "apple_private_key"

        # Mock JWT decode with wrong audience
        mock_jwt_decode.return_value = {
            "aud": "different_client_id",  # Wrong audience
            "sub": "apple_user_id",
            "email": "user@example.com",
            "exp": int(time.time()) + 3600
        }

        # Test token verification
        oauth_service = OAuthService()

        with pytest.raises(HTTPException) as exc_info:
            await oauth_service.verify_apple_token("valid_id_token")

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Invalid Apple token"

    @patch("app.services.oauth.settings")
    @patch("app.services.oauth.jwt.decode")
    async def test_verify_apple_token_expired(self, mock_jwt_decode, mock_settings):
        """Test Apple token verification with expired token."""
        # Mock settings
        mock_settings.APPLE_CLIENT_ID = "apple_client_id"
        mock_settings.APPLE_TEAM_ID = "apple_team_id"
        mock_settings.APPLE_KEY_ID = "apple_key_id"
        mock_settings.APPLE_PRIVATE_KEY = "apple_private_key"

        # Mock JWT decode with expired token
        mock_jwt_decode.return_value = {
            "aud": "apple_client_id",
            "sub": "apple_user_id",
            "email": "user@example.com",
            "exp": int(time.time()) - 3600  # Expired
        }

        # Test token verification
        oauth_service = OAuthService()

        with pytest.raises(HTTPException) as exc_info:
            await oauth_service.verify_apple_token("valid_id_token")

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Apple token expired"

    @patch("app.services.oauth.settings")
    @patch("app.services.oauth.jwt.decode")
    async def test_verify_apple_token_jwt_error(self, mock_jwt_decode, mock_settings):
        """Test Apple token verification with JWT decode error."""
        # Mock settings
        mock_settings.APPLE_CLIENT_ID = "apple_client_id"
        mock_settings.APPLE_TEAM_ID = "apple_team_id"
        mock_settings.APPLE_KEY_ID = "apple_key_id"
        mock_settings.APPLE_PRIVATE_KEY = "apple_private_key"

        # Mock JWT decode with error
        mock_jwt_decode.side_effect = Exception("Invalid token")

        # Test token verification
        oauth_service = OAuthService()

        with pytest.raises(HTTPException) as exc_info:
            await oauth_service.verify_apple_token("invalid_id_token")

        assert exc_info.value.status_code == 400
        assert "Failed to verify Apple token" in exc_info.value.detail


class TestOAuthProviderConfiguration:
    """Test OAuth provider configuration methods."""

    @patch("app.services.oauth.settings")
    def test_get_oauth_provider_config_google(self, mock_settings):
        """Test getting Google OAuth provider configuration."""
        # Mock settings
        mock_settings.GOOGLE_CLIENT_ID = "google_client_id"
        mock_settings.GOOGLE_CLIENT_SECRET = "google_client_secret"

        # Test provider config
        oauth_service = OAuthService()
        config = oauth_service.get_oauth_provider_config("google")

        # Verify config
        assert config["client_id"] == "google_client_id"
        assert config["authorization_url"] == "https://accounts.google.com/o/oauth2/v2/auth"
        assert config["token_url"] == "https://oauth2.googleapis.com/token"
        assert config["userinfo_url"] == "https://www.googleapis.com/oauth2/v2/userinfo"
        assert config["scope"] == "openid email profile"

    @patch("app.services.oauth.settings")
    def test_get_oauth_provider_config_apple(self, mock_settings):
        """Test getting Apple OAuth provider configuration."""
        # Mock settings
        mock_settings.APPLE_CLIENT_ID = "apple_client_id"
        mock_settings.APPLE_TEAM_ID = "apple_team_id"
        mock_settings.APPLE_KEY_ID = "apple_key_id"
        mock_settings.APPLE_PRIVATE_KEY = "apple_private_key"

        # Test provider config
        oauth_service = OAuthService()
        config = oauth_service.get_oauth_provider_config("apple")

        # Verify config
        assert config["client_id"] == "apple_client_id"
        assert config["authorization_url"] == "https://appleid.apple.com/auth/authorize"
        assert config["token_url"] == "https://appleid.apple.com/auth/token"
        assert config["scope"] == "name email"

    @patch("app.services.oauth.settings")
    def test_get_oauth_provider_config_unknown(self, mock_settings):
        """Test getting unknown OAuth provider configuration."""
        # Test provider config
        oauth_service = OAuthService()

        with pytest.raises(HTTPException) as exc_info:
            oauth_service.get_oauth_provider_config("unknown")

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Unsupported OAuth provider: unknown"

    @patch("app.services.oauth.settings")
    def test_is_provider_configured_google_true(self, mock_settings):
        """Test Google provider configuration check when configured."""
        # Mock settings
        mock_settings.GOOGLE_CLIENT_ID = "google_client_id"
        mock_settings.GOOGLE_CLIENT_SECRET = "google_client_secret"

        # Test provider configuration check
        oauth_service = OAuthService()
        result = oauth_service.is_provider_configured("google")

        # Verify result
        assert result is True

    @patch("app.services.oauth.settings")
    def test_is_provider_configured_google_false(self, mock_settings):
        """Test Google provider configuration check when not configured."""
        # Mock settings - missing Google config
        mock_settings.GOOGLE_CLIENT_ID = None
        mock_settings.GOOGLE_CLIENT_SECRET = None

        # Test provider configuration check
        oauth_service = OAuthService()
        result = oauth_service.is_provider_configured("google")

        # Verify result
        assert result is False

    @patch("app.services.oauth.settings")
    def test_is_provider_configured_apple_true(self, mock_settings):
        """Test Apple provider configuration check when configured."""
        # Mock settings
        mock_settings.APPLE_CLIENT_ID = "apple_client_id"
        mock_settings.APPLE_TEAM_ID = "apple_team_id"
        mock_settings.APPLE_KEY_ID = "apple_key_id"
        mock_settings.APPLE_PRIVATE_KEY = "apple_private_key"

        # Test provider configuration check
        oauth_service = OAuthService()
        result = oauth_service.is_provider_configured("apple")

        # Verify result
        assert result is True

    @patch("app.services.oauth.settings")
    def test_is_provider_configured_apple_false(self, mock_settings):
        """Test Apple provider configuration check when not configured."""
        # Mock settings - missing Apple config
        mock_settings.APPLE_CLIENT_ID = None
        mock_settings.APPLE_TEAM_ID = "apple_team_id"
        mock_settings.APPLE_KEY_ID = "apple_key_id"
        mock_settings.APPLE_PRIVATE_KEY = "apple_private_key"

        # Test provider configuration check
        oauth_service = OAuthService()
        result = oauth_service.is_provider_configured("apple")

        # Verify result
        assert result is False

    @patch("app.services.oauth.settings")
    def test_is_provider_configured_unknown(self, mock_settings):
        """Test unknown provider configuration check."""
        # Test provider configuration check
        oauth_service = OAuthService()
        result = oauth_service.is_provider_configured("unknown")

        # Verify result
        assert result is False


class TestOAuthIntegration:
    """Test OAuth integration scenarios."""

    @patch("app.services.oauth.settings")
    @patch("app.services.oauth.httpx.AsyncClient")
    @patch("app.services.oauth.jwt.decode")
    async def test_oauth_lifecycle_google(self, mock_jwt_decode, mock_client, mock_settings):
        """Test complete Google OAuth lifecycle."""
        # Mock settings
        mock_settings.GOOGLE_CLIENT_ID = "google_client_id"
        mock_settings.GOOGLE_CLIENT_SECRET = "google_client_secret"

        # Mock HTTP client with different responses for different calls
        mock_client_instance = AsyncMock()
        
        # First call: token verification response
        token_response = MagicMock()
        token_response.json.return_value = {
            "aud": "google_client_id",
            "sub": "google_user_id",
            "email": "user@gmail.com",
            "exp": int(time.time()) + 3600
        }
        token_response.raise_for_status.return_value = None
        
        # Second call: user info response
        user_info_response = MagicMock()
        user_info_response.json.return_value = {
            "id": "google_user_id",
            "email": "user@gmail.com",
            "name": "Test User"
        }
        user_info_response.raise_for_status.return_value = None
        
        # Set up the mock to return different responses for different calls
        mock_client_instance.get.side_effect = [token_response, user_info_response]
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # Test OAuth service
        oauth_service = OAuthService()

        # Test 1: Check if provider is configured
        is_configured = oauth_service.is_provider_configured("google")
        assert is_configured is True

        # Test 2: Get provider configuration
        config = oauth_service.get_oauth_provider_config("google")
        assert config["client_id"] == "google_client_id"

        # Test 3: Verify token
        token_data = await oauth_service.verify_google_token("valid_id_token")
        assert token_data["aud"] == "google_client_id"
        assert token_data["sub"] == "google_user_id"

        # Test 4: Get user info
        user_info = await oauth_service.get_google_user_info("valid_access_token")
        assert user_info["id"] == "google_user_id"
        assert user_info["email"] == "user@gmail.com"

        # Verify all calls were made
        assert mock_client_instance.get.call_count == 2  # Once for token verification, once for user info

    @patch("app.services.oauth.settings")
    @patch("app.services.oauth.jwt.decode")
    async def test_oauth_lifecycle_apple(self, mock_jwt_decode, mock_settings):
        """Test complete Apple OAuth lifecycle."""
        # Mock settings
        mock_settings.APPLE_CLIENT_ID = "apple_client_id"
        mock_settings.APPLE_TEAM_ID = "apple_team_id"
        mock_settings.APPLE_KEY_ID = "apple_key_id"
        mock_settings.APPLE_PRIVATE_KEY = "apple_private_key"

        # Mock JWT decode
        mock_jwt_decode.return_value = {
            "aud": "apple_client_id",
            "sub": "apple_user_id",
            "email": "user@example.com",
            "exp": int(time.time()) + 3600
        }

        # Test OAuth service
        oauth_service = OAuthService()

        # Test 1: Check if provider is configured
        is_configured = oauth_service.is_provider_configured("apple")
        assert is_configured is True

        # Test 2: Get provider configuration
        config = oauth_service.get_oauth_provider_config("apple")
        assert config["client_id"] == "apple_client_id"

        # Test 3: Verify token
        token_data = await oauth_service.verify_apple_token("valid_id_token")
        assert token_data["aud"] == "apple_client_id"
        assert token_data["sub"] == "apple_user_id"

        # Verify JWT decode was called
        mock_jwt_decode.assert_called_once() 