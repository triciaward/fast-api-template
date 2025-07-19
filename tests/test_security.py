from datetime import timedelta

import pytest
from jose import JWTError, jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)


class TestPasswordHashing:
    """Test password hashing and verification functions."""

    def test_password_hashing(self) -> None:
        """Test that passwords are properly hashed."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        # Hash should be different from original password
        assert hashed != password
        # Hash should be a string
        assert isinstance(hashed, str)
        # Hash should not be empty
        assert len(hashed) > 0

    def test_password_verification_success(self) -> None:
        """Test successful password verification."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        # Verification should succeed with correct password
        assert verify_password(password, hashed) is True

    def test_password_verification_failure(self) -> None:
        """Test failed password verification."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)

        # Verification should fail with wrong password
        assert verify_password(wrong_password, hashed) is False

    def test_different_passwords_different_hashes(self) -> None:
        """Test that different passwords produce different hashes."""
        password1 = "password1"
        password2 = "password2"

        hash1 = get_password_hash(password1)
        hash2 = get_password_hash(password2)

        # Different passwords should produce different hashes
        assert hash1 != hash2

    def test_same_password_different_hashes(self) -> None:
        """Test that same password produces different hashes (salt)."""
        password = "testpassword123"

        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Same password should produce different hashes due to salt
        assert hash1 != hash2
        # But both should verify successfully
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Test JWT token creation and validation."""

    def test_create_access_token(self) -> None:
        """Test creating a JWT access token."""
        email = "test@example.com"
        token = create_access_token(subject=email)

        # Token should be a string
        assert isinstance(token, str)
        # Token should not be empty
        assert len(token) > 0

        # Decode token to verify contents
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == email
        assert "exp" in payload

    def test_create_access_token_with_expires_delta(self) -> None:
        """Test creating a JWT token with custom expiration."""
        email = "test@example.com"
        expires_delta = timedelta(minutes=30)
        token = create_access_token(subject=email, expires_delta=expires_delta)

        # Decode token to verify contents
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == email
        assert "exp" in payload

    def test_token_expiration(self) -> None:
        """Test that expired tokens are properly handled."""
        email = "test@example.com"
        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)
        token = create_access_token(subject=email, expires_delta=expires_delta)

        # Token should be expired and raise JWTError
        with pytest.raises(JWTError):
            jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    def test_invalid_token_signature(self) -> None:
        """Test that tokens with invalid signatures are rejected."""
        email = "test@example.com"
        token = create_access_token(subject=email)

        # Try to decode with wrong secret key
        with pytest.raises(JWTError):
            jwt.decode(token, "wrong_secret_key", algorithms=[settings.ALGORITHM])

    def test_different_subjects_different_tokens(self) -> None:
        """Test that different subjects produce different tokens."""
        email1 = "test1@example.com"
        email2 = "test2@example.com"

        token1 = create_access_token(subject=email1)
        token2 = create_access_token(subject=email2)

        # Different subjects should produce different tokens
        assert token1 != token2

        # Verify both tokens decode correctly
        payload1 = jwt.decode(
            token1, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        payload2 = jwt.decode(
            token2, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        assert payload1["sub"] == email1
        assert payload2["sub"] == email2
