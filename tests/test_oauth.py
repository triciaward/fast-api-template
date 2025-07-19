from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException

from app.services.oauth import oauth_service


class TestOAuthService:
    def test_init(self) -> None:
        """Test OAuth service initialization."""
        assert oauth_service is not None
        assert hasattr(oauth_service, 'oauth')

    def test_is_provider_configured_google(self) -> None:
        """Test Google provider configuration check."""
        with patch('app.services.oauth.settings') as mock_settings:
            mock_settings.GOOGLE_CLIENT_ID = "test_client_id"
            mock_settings.GOOGLE_CLIENT_SECRET = "test_client_secret"

            assert oauth_service.is_provider_configured('google') is True

    def test_is_provider_configured_apple(self) -> None:
        """Test Apple provider configuration check."""
        with patch('app.services.oauth.settings') as mock_settings:
            mock_settings.APPLE_CLIENT_ID = "test_client_id"
            mock_settings.APPLE_TEAM_ID = "test_team_id"
            mock_settings.APPLE_KEY_ID = "test_key_id"
            mock_settings.APPLE_PRIVATE_KEY = "test_private_key"

            assert oauth_service.is_provider_configured('apple') is True

    def test_get_oauth_provider_config_google(self) -> None:
        """Test getting Google OAuth provider configuration."""
        with patch('app.services.oauth.settings') as mock_settings:
            mock_settings.GOOGLE_CLIENT_ID = "test_client_id"

            config = oauth_service.get_oauth_provider_config('google')
            assert config['client_id'] == "test_client_id"
            assert 'authorization_url' in config

    def test_get_oauth_provider_config_apple(self) -> None:
        """Test getting Apple OAuth provider configuration."""
        with patch('app.services.oauth.settings') as mock_settings:
            mock_settings.APPLE_CLIENT_ID = "test_client_id"

            config = oauth_service.get_oauth_provider_config('apple')
            assert config['client_id'] == "test_client_id"
            assert 'authorization_url' in config

    def test_get_oauth_provider_config_unsupported(self) -> None:
        """Test getting unsupported OAuth provider configuration."""
        with pytest.raises(HTTPException) as exc_info:
            oauth_service.get_oauth_provider_config('unsupported')
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_verify_google_token_success(self) -> None:
        """Test successful Google token verification."""
        with patch('app.services.oauth.settings') as mock_settings, \
                patch('httpx.AsyncClient') as mock_client:

            mock_settings.GOOGLE_CLIENT_ID = "test_client_id"

            mock_response = Mock()
            mock_response.json.return_value = {
                'aud': 'test_client_id',
                'email': 'test@example.com'
            }
            mock_response.raise_for_status.return_value = None

            mock_client_instance = Mock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(
                return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_client_instance

            result = await oauth_service.verify_google_token("test_token")
            assert result is not None
            assert result['aud'] == 'test_client_id'

    @pytest.mark.asyncio
    async def test_verify_google_token_invalid_audience(self) -> None:
        """Test Google token verification with invalid audience."""
        with patch('app.services.oauth.settings') as mock_settings, \
                patch('httpx.AsyncClient') as mock_client:

            mock_settings.GOOGLE_CLIENT_ID = "test_client_id"

            mock_response = Mock()
            mock_response.json.return_value = {
                'aud': 'wrong_client_id',
                'email': 'test@example.com'
            }
            mock_response.raise_for_status.return_value = None

            mock_client_instance = Mock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(
                return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_client_instance

            with pytest.raises(HTTPException) as exc_info:
                await oauth_service.verify_google_token("test_token")
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_verify_google_token_not_configured(self) -> None:
        """Test Google token verification when not configured."""
        with patch('app.services.oauth.settings') as mock_settings:
            mock_settings.GOOGLE_CLIENT_ID = None

            with pytest.raises(HTTPException) as exc_info:
                await oauth_service.verify_google_token("test_token")
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_verify_apple_token_success(self) -> None:
        """Test successful Apple token verification."""
        with patch('app.services.oauth.settings') as mock_settings, \
                patch('jwt.decode') as mock_jwt_decode, \
                patch('time.time') as mock_time:

            mock_settings.APPLE_CLIENT_ID = "test_client_id"
            mock_settings.APPLE_TEAM_ID = "test_team_id"
            mock_settings.APPLE_KEY_ID = "test_key_id"
            mock_settings.APPLE_PRIVATE_KEY = "test_private_key"

            mock_jwt_decode.return_value = {
                'aud': 'test_client_id',
                'exp': 9999999999  # Future timestamp
            }
            mock_time.return_value = 1000000000  # Past timestamp

            result = await oauth_service.verify_apple_token("test_token")
            assert result is not None
            assert result['aud'] == 'test_client_id'

    @pytest.mark.asyncio
    async def test_verify_apple_token_expired(self) -> None:
        """Test Apple token verification with expired token."""
        with patch('app.services.oauth.settings') as mock_settings, \
                patch('jwt.decode') as mock_jwt_decode, \
                patch('time.time') as mock_time:

            mock_settings.APPLE_CLIENT_ID = "test_client_id"
            mock_settings.APPLE_TEAM_ID = "test_team_id"
            mock_settings.APPLE_KEY_ID = "test_key_id"
            mock_settings.APPLE_PRIVATE_KEY = "test_private_key"

            mock_jwt_decode.return_value = {
                'aud': 'test_client_id',
                'exp': 1000000000  # Past timestamp
            }
            mock_time.return_value = 9999999999  # Future timestamp

            with pytest.raises(HTTPException) as exc_info:
                await oauth_service.verify_apple_token("test_token")
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_verify_apple_token_not_configured(self) -> None:
        """Test Apple token verification when not configured."""
        with patch('app.services.oauth.settings') as mock_settings:
            mock_settings.APPLE_CLIENT_ID = None

            with pytest.raises(HTTPException) as exc_info:
                await oauth_service.verify_apple_token("test_token")
            assert exc_info.value.status_code == 400


class TestOAuthServiceIntegration:
    def test_oauth_service_singleton(self) -> None:
        """Test that OAuth service is a singleton."""
        from app.services.oauth import oauth_service as service1
        from app.services.oauth import oauth_service as service2
        assert service1 is service2
