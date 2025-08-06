import base64
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def utc_now() -> datetime:
    """Get current UTC datetime (replaces deprecated datetime.utcnow())."""
    return datetime.now(timezone.utc)


def create_access_token(
    subject: str | Any, expires_delta: timedelta | None = None,
) -> str:
    if expires_delta:
        expire = utc_now() + expires_delta
    else:
        expire = utc_now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM,
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_refresh_token() -> str:
    """Create a cryptographically secure refresh token."""
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    """Hash a refresh token for secure storage."""
    return pwd_context.hash(token)


def verify_refresh_token(plain_token: str, hashed_token: str) -> bool:
    """Verify a refresh token against its hash."""
    return pwd_context.verify(plain_token, hashed_token)


# API Key functions
def generate_api_key() -> str:
    """Generate a cryptographically secure API key."""
    # Generate 32 random bytes and encode as base64
    key_bytes = secrets.token_bytes(32)
    # Convert to base64 and remove padding
    key_b64 = base64.urlsafe_b64encode(key_bytes).decode("ascii").rstrip("=")
    # Add prefix for easy identification
    return f"sk_{key_b64}"


def hash_api_key(key: str) -> str:
    """Hash an API key for secure storage."""
    return pwd_context.hash(key)


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash."""
    return pwd_context.verify(plain_key, hashed_key)
