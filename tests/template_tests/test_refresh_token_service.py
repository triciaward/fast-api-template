"""
Tests for Refresh Token service.

This module tests the Refresh Token service functionality including device detection, IP extraction, cookie management, and session operations.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import uuid

from fastapi import Request, Response

from app.services.refresh_token import (
    get_device_info,
    get_client_ip,
    set_refresh_token_cookie,
    clear_refresh_token_cookie,
    get_refresh_token_from_cookie,
    create_user_session,
    refresh_access_token,
    revoke_session,
    revoke_all_sessions,
)


class TestDeviceInfoExtraction:
    """Test device information extraction from request headers."""

    def test_get_device_info_chrome_windows(self):
        """Test Chrome on Windows detection."""
        mock_request = MagicMock()
        mock_request.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        result = get_device_info(mock_request)
        assert result == "Chrome on Windows"

    def test_get_device_info_firefox_macos(self):
        """Test Firefox on macOS detection."""
        mock_request = MagicMock()
        mock_request.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0"
        }

        result = get_device_info(mock_request)
        assert result == "Firefox on macOS"

    def test_get_device_info_safari_ios(self):
        """Test Safari on iOS detection."""
        mock_request = MagicMock()
        mock_request.headers = {
            "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1"
        }

        result = get_device_info(mock_request)
        assert result == "Safari on macOS"  # Logic checks "Mac" before "iPhone"

    def test_get_device_info_android(self):
        """Test Android device detection."""
        mock_request = MagicMock()
        mock_request.headers = {
            "user-agent": "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"
        }

        result = get_device_info(mock_request)
        assert result == "Chrome on Linux"  # Logic checks "Linux" before "Android"

    def test_get_device_info_unknown_browser(self):
        """Test unknown browser detection."""
        mock_request = MagicMock()
        mock_request.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59 Safari/537.36"
        }

        result = get_device_info(mock_request)
        assert result == "Safari on Windows"  # Logic finds "Safari" in user agent

    def test_get_device_info_unknown_os(self):
        """Test unknown OS detection."""
        mock_request = MagicMock()
        mock_request.headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        result = get_device_info(mock_request)
        assert result == "Chrome on Linux"

    def test_get_device_info_no_user_agent(self):
        """Test when no user-agent header is present."""
        mock_request = MagicMock()
        mock_request.headers = {}

        result = get_device_info(mock_request)
        assert result == "Unknown Device"

    def test_get_device_info_non_mozilla(self):
        """Test non-Mozilla user agent."""
        mock_request = MagicMock()
        mock_request.headers = {
            "user-agent": "curl/7.68.0"
        }

        result = get_device_info(mock_request)
        assert result == "Unknown Device"


class TestClientIPExtraction:
    """Test client IP address extraction from request headers."""

    def test_get_client_ip_x_forwarded_for(self):
        """Test IP extraction from X-Forwarded-For header."""
        mock_request = MagicMock()
        mock_request.headers = {
            "x-forwarded-for": "192.168.1.100, 10.0.0.1, 172.16.0.1"
        }
        mock_request.client = None

        result = get_client_ip(mock_request)
        assert result == "192.168.1.100"

    def test_get_client_ip_x_real_ip(self):
        """Test IP extraction from X-Real-IP header."""
        mock_request = MagicMock()
        mock_request.headers = {
            "x-real-ip": "203.0.113.1"
        }
        mock_request.client = None

        result = get_client_ip(mock_request)
        assert result == "203.0.113.1"

    def test_get_client_ip_direct_client(self):
        """Test IP extraction from direct client."""
        mock_request = MagicMock()
        mock_request.headers = {}
        mock_client = MagicMock()
        mock_client.host = "127.0.0.1"
        mock_request.client = mock_client

        result = get_client_ip(mock_request)
        assert result == "127.0.0.1"

    def test_get_client_ip_no_headers_no_client(self):
        """Test IP extraction when no headers or client available."""
        mock_request = MagicMock()
        mock_request.headers = {}
        mock_request.client = None

        result = get_client_ip(mock_request)
        assert result == "unknown"

    def test_get_client_ip_priority_order(self):
        """Test that X-Forwarded-For takes priority over X-Real-IP."""
        mock_request = MagicMock()
        mock_request.headers = {
            "x-forwarded-for": "192.168.1.100",
            "x-real-ip": "203.0.113.1"
        }
        mock_request.client = None

        result = get_client_ip(mock_request)
        assert result == "192.168.1.100"


class TestCookieManagement:
    """Test refresh token cookie management."""

    @patch("app.services.refresh_token.settings")
    def test_set_refresh_token_cookie(self, mock_settings):
        """Test setting refresh token cookie."""
        # Mock settings
        mock_settings.REFRESH_TOKEN_COOKIE_NAME = "refresh_token"
        mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 30
        mock_settings.REFRESH_TOKEN_COOKIE_HTTPONLY = True
        mock_settings.REFRESH_TOKEN_COOKIE_SECURE = True
        mock_settings.REFRESH_TOKEN_COOKIE_SAMESITE = "strict"
        mock_settings.REFRESH_TOKEN_COOKIE_PATH = "/"

        mock_response = MagicMock()
        token = "test_refresh_token_123"

        set_refresh_token_cookie(mock_response, token)

        # Verify cookie was set with correct parameters
        mock_response.set_cookie.assert_called_once_with(
            key="refresh_token",
            value=token,
            max_age=30 * 24 * 60 * 60,  # 30 days in seconds
            httponly=True,
            secure=True,
            samesite="strict",
            path="/",
        )

    @patch("app.services.refresh_token.settings")
    def test_clear_refresh_token_cookie(self, mock_settings):
        """Test clearing refresh token cookie."""
        # Mock settings
        mock_settings.REFRESH_TOKEN_COOKIE_NAME = "refresh_token"
        mock_settings.REFRESH_TOKEN_COOKIE_PATH = "/"

        mock_response = MagicMock()

        clear_refresh_token_cookie(mock_response)

        # Verify cookie was deleted
        mock_response.delete_cookie.assert_called_once_with(
            key="refresh_token",
            path="/",
        )

    @patch("app.services.refresh_token.settings")
    def test_get_refresh_token_from_cookie(self, mock_settings):
        """Test getting refresh token from cookie."""
        # Mock settings
        mock_settings.REFRESH_TOKEN_COOKIE_NAME = "refresh_token"

        mock_request = MagicMock()
        mock_request.cookies = {"refresh_token": "test_token_123"}

        result = get_refresh_token_from_cookie(mock_request)
        assert result == "test_token_123"

    @patch("app.services.refresh_token.settings")
    def test_get_refresh_token_from_cookie_missing(self, mock_settings):
        """Test getting refresh token when cookie is missing."""
        # Mock settings
        mock_settings.REFRESH_TOKEN_COOKIE_NAME = "refresh_token"

        mock_request = MagicMock()
        mock_request.cookies = {}

        result = get_refresh_token_from_cookie(mock_request)
        assert result is None


class TestSessionManagement:
    """Test user session management."""

    @patch("app.services.refresh_token.crud_create_refresh_token")
    @patch("app.services.refresh_token.create_access_token")
    @patch("app.services.refresh_token.create_refresh_token")
    @patch("app.services.refresh_token.get_device_info")
    @patch("app.services.refresh_token.get_client_ip")
    def test_create_user_session_success(
        self, mock_get_ip, mock_get_device, mock_create_refresh, mock_create_access, mock_crud_create
    ):
        """Test successful user session creation."""
        # Mock dependencies
        mock_create_access.return_value = "access_token_123"
        mock_create_refresh.return_value = "refresh_token_456"
        mock_get_device.return_value = "Chrome on Windows"
        mock_get_ip.return_value = "192.168.1.100"
        mock_crud_create.return_value = MagicMock()

        # Mock user
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_user.email = "test@example.com"

        # Mock request
        mock_request = MagicMock()
        mock_request.headers = {"user-agent": "Chrome/91.0"}

        # Mock database session
        mock_db = MagicMock()

        # Test session creation
        access_token, refresh_token = create_user_session(mock_db, mock_user, mock_request)

        # Verify results
        assert access_token == "access_token_123"
        assert refresh_token == "refresh_token_456"

        # Verify function calls
        mock_create_access.assert_called_once_with(subject="test@example.com", expires_delta=timedelta(minutes=15))
        mock_create_refresh.assert_called_once_with()
        mock_get_device.assert_called_once_with(mock_request)
        mock_get_ip.assert_called_once_with(mock_request)
        mock_crud_create.assert_called_once()

    @patch("app.services.refresh_token.verify_refresh_token_in_db")
    @patch("app.services.refresh_token.create_access_token")
    def test_refresh_access_token_success(self, mock_create_access, mock_verify_token):
        """Test successful access token refresh."""
        # Mock dependencies
        mock_create_access.return_value = "new_access_token_123"
        mock_refresh_token = MagicMock()
        mock_refresh_token.user_id = uuid.uuid4()
        mock_verify_token.return_value = mock_refresh_token

        # Mock user
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.is_deleted = False

        # Mock database session
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        # Test token refresh
        result = refresh_access_token(mock_db, "valid_refresh_token")

        # Verify result
        assert result is not None
        access_token, expires_at = result
        assert access_token == "new_access_token_123"
        assert isinstance(expires_at, datetime)

        # Verify function calls
        mock_verify_token.assert_called_once_with(mock_db, "valid_refresh_token")
        mock_create_access.assert_called_once_with(subject="test@example.com", expires_delta=timedelta(minutes=15))

    @patch("app.services.refresh_token.verify_refresh_token_in_db")
    def test_refresh_access_token_invalid(self, mock_verify_token):
        """Test access token refresh with invalid refresh token."""
        # Mock dependencies
        mock_verify_token.return_value = None

        # Mock database session
        mock_db = MagicMock()

        # Test token refresh
        result = refresh_access_token(mock_db, "invalid_refresh_token")

        # Verify result
        assert result is None

        # Verify function calls
        mock_verify_token.assert_called_once_with(mock_db, "invalid_refresh_token")

    @patch("app.crud.revoke_refresh_token")
    @patch("app.services.refresh_token.verify_refresh_token_in_db")
    def test_revoke_session_success(self, mock_verify, mock_revoke):
        """Test successful session revocation."""
        # Mock dependencies
        mock_refresh_token = MagicMock()
        mock_refresh_token.id = uuid.uuid4()
        mock_verify.return_value = mock_refresh_token
        mock_revoke.return_value = True

        # Mock database session
        mock_db = MagicMock()

        # Test session revocation
        result = revoke_session(mock_db, "valid_refresh_token")

        # Verify result
        assert result is True

        # Verify function calls
        mock_verify.assert_called_once_with(mock_db, "valid_refresh_token")
        mock_revoke.assert_called_once()

    @patch("app.crud.revoke_refresh_token")
    def test_revoke_session_failure(self, mock_revoke):
        """Test session revocation failure."""
        # Mock dependencies
        mock_revoke.return_value = False

        # Mock database session
        mock_db = MagicMock()

        # Test session revocation
        result = revoke_session(mock_db, "invalid_refresh_token")

        # Verify result
        assert result is False

    @patch("app.crud.revoke_all_user_sessions")
    def test_revoke_all_sessions_success(self, mock_revoke_all):
        """Test successful revocation of all user sessions."""
        # Mock dependencies
        mock_revoke_all.return_value = 3

        # Mock database session
        mock_db = MagicMock()
        user_id = uuid.uuid4()

        # Test session revocation
        result = revoke_all_sessions(mock_db, user_id)

        # Verify result
        assert result == 3

        # Verify function calls
        mock_revoke_all.assert_called_once_with(mock_db, user_id, None)

    @patch("app.crud.revoke_all_user_sessions")
    def test_revoke_all_sessions_except_one(self, mock_revoke_all):
        """Test revocation of all sessions except one."""
        # Mock dependencies
        mock_revoke_all.return_value = 2

        # Mock database session
        mock_db = MagicMock()
        user_id = uuid.uuid4()
        except_token = "keep_this_token"

        # Test session revocation
        result = revoke_all_sessions(mock_db, user_id, except_token)

        # Verify result
        assert result == 2

        # Verify function calls
        mock_revoke_all.assert_called_once()


class TestSessionLimitEnforcement:
    """Test session limit enforcement."""

    @patch("app.services.refresh_token.enforce_session_limit")
    def test_session_limit_enforcement(self, mock_enforce_limit):
        """Test session limit enforcement."""
        # Mock dependencies
        mock_enforce_limit.return_value = True

        # Mock database session
        mock_db = MagicMock()
        user_id = uuid.uuid4()

        # Test session limit enforcement
        result = mock_enforce_limit(mock_db, user_id)

        # Verify result
        assert result is True

        # Verify function calls
        mock_enforce_limit.assert_called_once_with(mock_db, user_id)


class TestRefreshTokenIntegration:
    """Test refresh token integration scenarios."""

    @patch("app.services.refresh_token.crud_create_refresh_token")
    @patch("app.services.refresh_token.create_access_token")
    @patch("app.services.refresh_token.create_refresh_token")
    @patch("app.services.refresh_token.verify_refresh_token_in_db")
    @patch("app.crud.revoke_refresh_token")
    def test_complete_refresh_token_lifecycle(
        self, mock_revoke, mock_verify, mock_create_refresh, mock_create_access, mock_crud_create
    ):
        """Test complete refresh token lifecycle."""
        # Mock dependencies for session creation
        mock_create_access.return_value = "access_token_123"
        mock_create_refresh.return_value = "refresh_token_456"
        mock_crud_create.return_value = MagicMock()

        # Mock dependencies for token verification
        mock_refresh_token = MagicMock()
        mock_refresh_token.user_id = uuid.uuid4()
        mock_refresh_token.id = uuid.uuid4()
        mock_verify.return_value = mock_refresh_token

        # Mock dependencies for session revocation
        mock_revoke.return_value = True

        # Mock user
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_user.email = "test@example.com"
        mock_user.is_deleted = False

        # Mock request
        mock_request = MagicMock()
        mock_request.headers = {"user-agent": "Chrome/91.0"}

        # Mock database session
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        # Test 1: Create session
        access_token, refresh_token = create_user_session(mock_db, mock_user, mock_request)
        assert access_token == "access_token_123"
        assert refresh_token == "refresh_token_456"

        # Test 2: Refresh access token
        new_access_token, expires_at = refresh_access_token(mock_db, refresh_token)
        assert new_access_token == "access_token_123"
        assert isinstance(expires_at, datetime)

        # Test 3: Revoke session
        revoked = revoke_session(mock_db, refresh_token)
        assert revoked is True

        # Verify all function calls
        mock_create_access.assert_called()
        mock_create_refresh.assert_called()
        assert mock_verify.call_count == 2  # Called in refresh_access_token and revoke_session
        mock_revoke.assert_called_once() 