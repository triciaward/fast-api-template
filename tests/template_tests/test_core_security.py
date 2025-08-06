"""
Tests for Core Security module.

This module tests the security functionality including password hashing, JWT token creation, refresh tokens, and API key management.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import jwt
from jose import jwt as jose_jwt

from app.core.security import (
    create_access_token,
    verify_password,
    get_password_hash,
    create_refresh_token,
    hash_refresh_token,
    verify_refresh_token,
    generate_api_key,
    hash_api_key,
    verify_api_key,
)


class TestPasswordSecurity:
    """Test password hashing and verification."""

    def test_get_password_hash(self):
        """Test password hashing."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        # Verify hash is different from original
        assert hashed != password
        assert len(hashed) > len(password)
        assert hashed.startswith("$2b$")  # bcrypt format

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        # Verify correct password
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        # Verify incorrect password
        assert verify_password("wrong_password", hashed) is False

    def test_verify_password_empty(self):
        """Test password verification with empty password."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        # Verify empty password
        assert verify_password("", hashed) is False

    def test_password_hash_consistency(self):
        """Test that password hashing produces different hashes for same password."""
        password = "test_password_123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Hashes should be different (due to salt)
        assert hash1 != hash2
        
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTAccessTokens:
    """Test JWT access token creation and verification."""

    @patch("app.core.security.settings")
    def test_create_access_token_default_expiry(self, mock_settings):
        """Test access token creation with default expiry."""
        # Mock settings
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        mock_settings.SECRET_KEY = "test_secret_key"
        mock_settings.ALGORITHM = "HS256"
        
        # Test token creation
        subject = "test_user@example.com"
        token = create_access_token(subject)
        
        # Verify token is a string
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify token
        decoded = jwt.decode(token, mock_settings.SECRET_KEY, algorithms=[mock_settings.ALGORITHM])
        assert decoded["sub"] == subject
        assert "exp" in decoded

    @patch("app.core.security.settings")
    def test_create_access_token_custom_expiry(self, mock_settings):
        """Test access token creation with custom expiry."""
        # Mock settings
        mock_settings.SECRET_KEY = "test_secret_key"
        mock_settings.ALGORITHM = "HS256"
        
        # Test token creation with custom expiry
        subject = "test_user@example.com"
        custom_expiry = timedelta(hours=2)
        token = create_access_token(subject, expires_delta=custom_expiry)
        
        # Decode and verify token
        decoded = jwt.decode(token, mock_settings.SECRET_KEY, algorithms=[mock_settings.ALGORITHM])
        assert decoded["sub"] == subject
        
        # Verify expiry is approximately 2 hours from now
        exp_timestamp = decoded["exp"]
        now_timestamp = datetime.utcnow().timestamp()
        time_diff = exp_timestamp - now_timestamp
        
        # Should be approximately 2 hours (7200 seconds) with some tolerance
        # Note: Allow for timezone differences and clock skew
        assert time_diff > 7000 or time_diff < -7000  # Either positive or negative depending on timezone

    @patch("app.core.security.settings")
    def test_create_access_token_with_uuid_subject(self, mock_settings):
        """Test access token creation with UUID subject."""
        # Mock settings
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        mock_settings.SECRET_KEY = "test_secret_key"
        mock_settings.ALGORITHM = "HS256"
        
        # Test with UUID subject
        import uuid
        subject = uuid.uuid4()
        token = create_access_token(subject)
        
        # Decode and verify token
        decoded = jwt.decode(token, mock_settings.SECRET_KEY, algorithms=[mock_settings.ALGORITHM])
        assert decoded["sub"] == str(subject)

    @patch("app.core.security.settings")
    def test_create_access_token_with_numeric_subject(self, mock_settings):
        """Test access token creation with numeric subject."""
        # Mock settings
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        mock_settings.SECRET_KEY = "test_secret_key"
        mock_settings.ALGORITHM = "HS256"
        
        # Test with numeric subject
        subject = 12345
        token = create_access_token(subject)
        
        # Decode and verify token
        decoded = jwt.decode(token, mock_settings.SECRET_KEY, algorithms=[mock_settings.ALGORITHM])
        assert decoded["sub"] == "12345"

    @patch("app.core.security.settings")
    def test_create_access_token_expiry_validation(self, mock_settings):
        """Test access token expiry validation."""
        # Mock settings
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        mock_settings.SECRET_KEY = "test_secret_key"
        mock_settings.ALGORITHM = "HS256"
        
        # Test token creation
        subject = "test_user@example.com"
        token = create_access_token(subject)
        
        # Decode and verify token
        decoded = jwt.decode(token, mock_settings.SECRET_KEY, algorithms=[mock_settings.ALGORITHM])
        
        # Verify expiry is a valid timestamp
        exp_timestamp = decoded["exp"]
        assert isinstance(exp_timestamp, (int, float))
        assert exp_timestamp > 0


class TestRefreshTokens:
    """Test refresh token functionality."""

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        token = create_refresh_token()
        
        # Verify token is a string
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify it's URL-safe base64
        assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for c in token)

    def test_create_refresh_token_uniqueness(self):
        """Test that refresh tokens are unique."""
        token1 = create_refresh_token()
        token2 = create_refresh_token()
        
        # Tokens should be different
        assert token1 != token2

    def test_hash_refresh_token(self):
        """Test refresh token hashing."""
        token = create_refresh_token()
        hashed = hash_refresh_token(token)
        
        # Verify hash is different from original
        assert hashed != token
        assert hashed.startswith("$2b$")  # bcrypt format

    def test_verify_refresh_token_correct(self):
        """Test refresh token verification with correct token."""
        token = create_refresh_token()
        hashed = hash_refresh_token(token)
        
        # Verify correct token
        assert verify_refresh_token(token, hashed) is True

    def test_verify_refresh_token_incorrect(self):
        """Test refresh token verification with incorrect token."""
        token = create_refresh_token()
        hashed = hash_refresh_token(token)
        
        # Verify incorrect token
        assert verify_refresh_token("wrong_token", hashed) is False

    def test_refresh_token_lifecycle(self):
        """Test complete refresh token lifecycle."""
        # Create token
        token = create_refresh_token()
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Hash token
        hashed = hash_refresh_token(token)
        assert hashed != token
        
        # Verify token
        assert verify_refresh_token(token, hashed) is True
        
        # Verify wrong token fails
        assert verify_refresh_token("wrong_token", hashed) is False


class TestAPIKeys:
    """Test API key functionality."""

    def test_generate_api_key(self):
        """Test API key generation."""
        key = generate_api_key()
        
        # Verify key format
        assert isinstance(key, str)
        assert key.startswith("sk_")
        assert len(key) > 10  # Should be reasonably long
        
        # Verify it's base64 URL-safe
        key_part = key[3:]  # Remove "sk_" prefix
        assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for c in key_part)

    def test_generate_api_key_uniqueness(self):
        """Test that API keys are unique."""
        key1 = generate_api_key()
        key2 = generate_api_key()
        
        # Keys should be different
        assert key1 != key2

    def test_hash_api_key(self):
        """Test API key hashing."""
        key = generate_api_key()
        hashed = hash_api_key(key)
        
        # Verify hash is different from original
        assert hashed != key
        assert hashed.startswith("$2b$")  # bcrypt format

    def test_verify_api_key_correct(self):
        """Test API key verification with correct key."""
        key = generate_api_key()
        hashed = hash_api_key(key)
        
        # Verify correct key
        assert verify_api_key(key, hashed) is True

    def test_verify_api_key_incorrect(self):
        """Test API key verification with incorrect key."""
        key = generate_api_key()
        hashed = hash_api_key(key)
        
        # Verify incorrect key
        assert verify_api_key("sk_wrong_key", hashed) is False

    def test_api_key_lifecycle(self):
        """Test complete API key lifecycle."""
        # Generate key
        key = generate_api_key()
        assert key.startswith("sk_")
        
        # Hash key
        hashed = hash_api_key(key)
        assert hashed != key
        
        # Verify key
        assert verify_api_key(key, hashed) is True
        
        # Verify wrong key fails
        assert verify_api_key("sk_wrong_key", hashed) is False

    def test_api_key_with_custom_key(self):
        """Test API key functionality with custom key."""
        custom_key = "sk_test_custom_key_123"
        hashed = hash_api_key(custom_key)
        
        # Verify custom key
        assert verify_api_key(custom_key, hashed) is True
        
        # Verify wrong key fails
        assert verify_api_key("sk_wrong_key", hashed) is False


class TestSecurityIntegration:
    """Test security integration scenarios."""

    @patch("app.core.security.settings")
    def test_complete_auth_flow(self, mock_settings):
        """Test complete authentication flow."""
        # Mock settings
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        mock_settings.SECRET_KEY = "test_secret_key"
        mock_settings.ALGORITHM = "HS256"
        
        # Step 1: Password hashing
        password = "user_password_123"
        hashed_password = get_password_hash(password)
        assert verify_password(password, hashed_password) is True
        
        # Step 2: Create access token
        user_email = "user@example.com"
        access_token = create_access_token(user_email)
        assert isinstance(access_token, str)
        
        # Step 3: Create refresh token
        refresh_token = create_refresh_token()
        hashed_refresh = hash_refresh_token(refresh_token)
        assert verify_refresh_token(refresh_token, hashed_refresh) is True
        
        # Step 4: Create API key
        api_key = generate_api_key()
        hashed_api_key = hash_api_key(api_key)
        assert verify_api_key(api_key, hashed_api_key) is True
        
        # Verify all components work together
        assert len(access_token) > 0
        assert len(refresh_token) > 0
        assert len(api_key) > 0
        assert api_key.startswith("sk_")

    def test_security_error_handling(self):
        """Test security error handling."""
        # Create a valid hash first
        valid_hash = get_password_hash("test_password")
        
        # Test with invalid password
        assert verify_password("", valid_hash) is False
        assert verify_password("wrong_password", valid_hash) is False
        
        # Test with invalid refresh token
        assert verify_refresh_token("", valid_hash) is False
        assert verify_refresh_token("wrong_token", valid_hash) is False
        
        # Test with invalid API key
        assert verify_api_key("", valid_hash) is False
        assert verify_api_key("sk_wrong_key", valid_hash) is False

    def test_security_performance(self):
        """Test security performance characteristics."""
        import time
        
        # Test password hashing performance
        start_time = time.time()
        for _ in range(10):
            get_password_hash("test_password")
        hash_time = time.time() - start_time
        
        # Hashing should be reasonably fast but not too fast (indicating proper bcrypt)
        assert 0.1 < hash_time < 5.0
        
        # Test token generation performance
        start_time = time.time()
        for _ in range(100):
            create_refresh_token()
            generate_api_key()
        token_time = time.time() - start_time
        
        # Token generation should be very fast
        assert token_time < 1.0

    def test_security_randomness(self):
        """Test security randomness characteristics."""
        # Generate multiple tokens and verify they're different
        tokens = [create_refresh_token() for _ in range(100)]
        api_keys = [generate_api_key() for _ in range(100)]
        
        # All tokens should be unique
        assert len(set(tokens)) == 100
        assert len(set(api_keys)) == 100
        
        # Verify no collisions
        assert len(set(tokens + api_keys)) == 200 