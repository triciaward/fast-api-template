"""Shared test utilities for authentication tests."""

import types


def create_test_user(
    user_id: str = "11111111-1111-1111-1111-111111111111",
    email: str = "test@example.com",
    username: str = "testuser",
    is_verified: bool = True,
    is_superuser: bool = False,
    is_deleted: bool = False,
    has_password: bool = True,
    oauth_provider: str | None = None,
    oauth_id: str | None = None,
    oauth_email: str | None = None,
) -> types.SimpleNamespace:
    """Create a test user object with sensible defaults."""
    return types.SimpleNamespace(
        id=user_id,
        email=email,
        username=username,
        is_verified=is_verified,
        is_superuser=is_superuser,
        is_deleted=is_deleted,
        hashed_password="test_hash" if has_password else None,
        oauth_provider=oauth_provider,
        oauth_id=oauth_id,
        oauth_email=oauth_email,
        created_at="2024-01-01T00:00:00Z",
        deletion_requested_at=None,
        deletion_confirmed_at=None,
        deletion_scheduled_for=None,
    )


def create_admin_user(
    user_id: str = "00000000-0000-0000-0000-000000000001",
    email: str = "admin@example.com",
    username: str = "admin",
) -> types.SimpleNamespace:
    """Create a test admin user."""
    return create_test_user(
        user_id=user_id,
        email=email,
        username=username,
        is_superuser=True,
        is_verified=True,
    )


class MockEmailService:
    """Mock email service for testing."""

    def __init__(self, configured: bool = True):
        self._configured = configured

    def is_configured(self) -> bool:
        return self._configured

    async def create_verification_token(self, db, user_id: str) -> str | None:
        return "verification_token_123" if self._configured else None

    def send_verification_email(self, email: str, username: str, token: str) -> None:
        pass

    async def create_password_reset_token(self, db, user_id: str) -> str | None:
        return "reset_token_123" if self._configured else None

    def send_password_reset_email(self, email: str, username: str, token: str) -> bool:
        return self._configured

    async def verify_password_reset_token(self, db, token: str) -> str | None:
        if token == "valid_token":
            return "11111111-1111-1111-1111-111111111111"
        return None


class MockOAuthService:
    """Mock OAuth service for testing."""

    def __init__(self, configured_providers: list[str] | None = None):
        self.configured_providers = configured_providers or ["google", "apple"]

    def is_provider_configured(self, provider: str) -> bool:
        return provider in self.configured_providers

    async def verify_google_token(self, token: str) -> dict | None:
        if token == "valid_google_token":
            return {"sub": "google_user_123", "email": "user@gmail.com"}
        return None

    async def verify_apple_token(self, token: str) -> dict | None:
        if token == "valid_apple_token":
            return {"sub": "apple_user_123", "email": "user@icloud.com"}
        return None


def mock_authentication_success(monkeypatch, user: types.SimpleNamespace | None = None):
    """Mock successful authentication."""
    if user is None:
        user = create_test_user()

    from app.api.auth import login as login_module

    async def fake_authenticate_user(db, email: str, password: str):
        return user

    async def fake_log_login_attempt(db, request, user=None, success: bool = False):
        return None

    async def fake_create_user_session(db, user, request):
        return "access_token_123", "refresh_token_123"

    monkeypatch.setattr(
        login_module.crud_user, "authenticate_user", fake_authenticate_user
    )
    monkeypatch.setattr(login_module, "log_login_attempt", fake_log_login_attempt)

    from app.services.auth import refresh_token as rt

    monkeypatch.setattr(rt, "create_user_session", fake_create_user_session)

    return user


def mock_authentication_failure(monkeypatch, reason: str = "invalid_credentials"):
    """Mock authentication failure for various reasons."""
    from app.api.auth import login as login_module

    async def fake_authenticate_user(db, email: str, password: str):
        if reason == "invalid_credentials":
            return None
        if reason == "unverified":
            return create_test_user(is_verified=False)
        if reason == "exception":
            raise Exception("Database error")
        return None

    async def fake_log_login_attempt(db, request, user=None, success: bool = False):
        return None

    monkeypatch.setattr(
        login_module.crud_user, "authenticate_user", fake_authenticate_user
    )
    monkeypatch.setattr(login_module, "log_login_attempt", fake_log_login_attempt)


def override_dependency(app, dependency, replacement):
    """Helper to override FastAPI dependencies in tests."""
    app.dependency_overrides[dependency] = replacement
    return lambda: app.dependency_overrides.pop(dependency, None)


async def fake_get_user_by_email(db, email: str) -> types.SimpleNamespace | None:
    """Common fake function for user lookup by email."""
    return None


async def fake_get_user_by_username(db, username: str) -> types.SimpleNamespace | None:
    """Common fake function for user lookup by username."""
    return None


async def fake_create_user(db, user) -> types.SimpleNamespace:
    """Common fake function for user creation."""
    return create_test_user(
        email=user.email,
        username=user.username,
        is_verified=False,
    )
