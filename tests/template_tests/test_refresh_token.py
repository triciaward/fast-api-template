import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_refresh_token,
    hash_refresh_token,
    verify_refresh_token,
)
from app.crud import (
    cleanup_expired_tokens,
    enforce_session_limit,
    get_refresh_token_by_hash,
    get_user_session_count,
    get_user_sessions,
    revoke_all_user_sessions,
    revoke_refresh_token,
    verify_refresh_token_in_db,
)
from app.crud import (
    create_refresh_token as crud_create_refresh_token,
)
from app.models import RefreshToken, User
from app.services.refresh_token import (
    clear_refresh_token_cookie,
    create_user_session,
    get_client_ip,
    get_device_info,
    get_refresh_token_from_cookie,
    refresh_access_token,
    revoke_all_sessions,
    revoke_session,
    set_refresh_token_cookie,
)


class TestRefreshTokenSecurity:
    """Test refresh token security functions."""

    def test_create_refresh_token(self):
        """Test that refresh tokens are created correctly."""
        token1 = create_refresh_token()
        token2 = create_refresh_token()

        assert len(token1) == 43  # base64 encoded 32 bytes
        assert len(token2) == 43
        assert token1 != token2  # Tokens should be unique

    def test_hash_refresh_token(self):
        """Test that refresh tokens are hashed correctly."""
        token = create_refresh_token()
        hashed = hash_refresh_token(token)

        assert hashed != token
        assert len(hashed) > len(token)
        assert hashed.startswith("$2b$")  # bcrypt hash

    def test_verify_refresh_token(self):
        """Test that refresh token verification works."""
        token = create_refresh_token()
        hashed = hash_refresh_token(token)

        assert verify_refresh_token(token, hashed) is True
        assert verify_refresh_token("wrong_token", hashed) is False


@pytest.mark.skip(
    reason="Requires complex refresh token functionality - not implemented yet"
)
class TestRefreshTokenCRUD:
    """Test refresh token CRUD operations."""

    def test_create_refresh_token_crud(self, sync_db_session: Session):
        """Test creating a refresh token in the database."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            username="testuser",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        token = create_refresh_token()
        db_refresh_token = crud_create_refresh_token(
            sync_db_session, uuid.UUID(str(user.id)), token, "Test Device", "127.0.0.1"
        )

        assert db_refresh_token.user_id == user.id
        # Verify that the stored hash can be used to verify the original token
        assert verify_refresh_token(token, str(db_refresh_token.token_hash))
        assert db_refresh_token.device_info == "Test Device"
        assert db_refresh_token.ip_address == "127.0.0.1"
        assert db_refresh_token.is_revoked is False
        assert db_refresh_token.expires_at > datetime.utcnow()

    def test_get_refresh_token_by_hash(self, sync_db_session: Session):
        """Test retrieving a refresh token by hash."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            username="testuser",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        token = create_refresh_token()
        db_refresh_token = crud_create_refresh_token(
            sync_db_session, uuid.UUID(str(user.id)), token
        )

        # Test valid token - use verify_refresh_token_in_db instead
        retrieved = verify_refresh_token_in_db(sync_db_session, token)
        assert retrieved is not None
        assert retrieved.id == db_refresh_token.id

        # Test invalid hash
        retrieved = get_refresh_token_by_hash(sync_db_session, "invalid_hash")
        assert retrieved is None

    def test_verify_refresh_token_in_db(self, sync_db_session: Session):
        """Test verifying a refresh token against the database."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            username="testuser",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        token = create_refresh_token()
        crud_create_refresh_token(sync_db_session, uuid.UUID(str(user.id)), token)

        # Test valid token
        result = verify_refresh_token_in_db(sync_db_session, token)
        assert result is not None
        assert result.user_id == user.id

        # Test invalid token
        result = verify_refresh_token_in_db(sync_db_session, "invalid_token")
        assert result is None

    def test_revoke_refresh_token(self, sync_db_session: Session):
        """Test revoking a refresh token."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            username="testuser",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        token = create_refresh_token()
        db_refresh_token = crud_create_refresh_token(
            sync_db_session, uuid.UUID(str(user.id)), token
        )

        # Revoke token
        success = revoke_refresh_token(
            sync_db_session, uuid.UUID(str(db_refresh_token.id))
        )
        assert success is True

        # Verify token is revoked
        sync_db_session.refresh(db_refresh_token)
        assert db_refresh_token.is_revoked is True

        # Test revoking non-existent token
        success = revoke_refresh_token(sync_db_session, uuid.uuid4())
        assert success is False

    def test_revoke_refresh_token_by_hash(self, sync_db_session: Session):
        """Test revoking a refresh token by hash."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            username="testuser",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        token = create_refresh_token()
        crud_create_refresh_token(sync_db_session, uuid.UUID(str(user.id)), token)

        # Revoke token - use revoke_session instead
        success = revoke_session(sync_db_session, token)
        assert success is True

        # Verify token is no longer valid
        result = verify_refresh_token_in_db(sync_db_session, token)
        assert result is None

    def test_get_user_sessions(self, sync_db_session: Session):
        """Test getting user sessions."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            username="testuser",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        # Create multiple sessions
        token1 = create_refresh_token()
        token2 = create_refresh_token()
        db_token1 = crud_create_refresh_token(
            sync_db_session, uuid.UUID(str(user.id)), token1, "Device 1"
        )
        crud_create_refresh_token(
            sync_db_session, uuid.UUID(str(user.id)), token2, "Device 2"
        )

        sessions = get_user_sessions(sync_db_session, uuid.UUID(str(user.id)))
        assert len(sessions) == 2

        # Test with current session ID
        sessions = get_user_sessions(
            sync_db_session, uuid.UUID(str(user.id)), uuid.UUID(str(db_token1.id))
        )
        assert len(sessions) == 2
        # Check that current session is marked
        current_session = next(s for s in sessions if s.id == db_token1.id)
        assert getattr(current_session, "is_current", False) is True

    def test_get_user_session_count(self, sync_db_session: Session):
        """Test getting user session count."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            username="testuser",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        # Create sessions
        crud_create_refresh_token(
            sync_db_session, uuid.UUID(str(user.id)), create_refresh_token()
        )
        crud_create_refresh_token(
            sync_db_session, uuid.UUID(str(user.id)), create_refresh_token()
        )

        count = get_user_session_count(sync_db_session, uuid.UUID(str(user.id)))
        assert count == 2

    def test_cleanup_expired_tokens(self, sync_db_session: Session):
        """Test cleaning up expired tokens."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            username="testuser",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        # Create expired token
        token = create_refresh_token()
        db_refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(token),
            expires_at=datetime.utcnow() - timedelta(days=1),
            is_revoked=False,
        )
        sync_db_session.add(db_refresh_token)
        sync_db_session.commit()

        # Cleanup expired tokens
        deleted_count = cleanup_expired_tokens(sync_db_session)
        assert deleted_count == 1

        # Verify token is deleted
        result = (
            sync_db_session.query(RefreshToken)
            .filter_by(id=db_refresh_token.id)
            .first()
        )
        assert result is None

    @pytest.mark.refresh_token
    def test_enforce_session_limit(self, sync_db_session: Session):
        """Test enforcing session limits."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            username="testuser",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        # Create more sessions than the limit
        original_limit = settings.MAX_SESSIONS_PER_USER
        settings.MAX_SESSIONS_PER_USER = 2

        try:
            # Create 3 sessions
            token1 = create_refresh_token()
            token2 = create_refresh_token()
            token3 = create_refresh_token()

            db_token1 = crud_create_refresh_token(
                sync_db_session, uuid.UUID(str(user.id)), token1
            )
            db_token2 = crud_create_refresh_token(
                sync_db_session, uuid.UUID(str(user.id)), token2
            )
            db_token3 = crud_create_refresh_token(
                sync_db_session, uuid.UUID(str(user.id)), token3
            )

            # Enforce limit with the newest token
            enforce_session_limit(
                sync_db_session, uuid.UUID(str(user.id)), uuid.UUID(str(db_token3.id))
            )

            # Check that oldest session is revoked
            sync_db_session.refresh(db_token1)
            assert db_token1.is_revoked is True

            # Check that newer sessions are still active
            sync_db_session.refresh(db_token2)
            sync_db_session.refresh(db_token3)
            assert db_token2.is_revoked is False
            assert db_token3.is_revoked is False

        finally:
            settings.MAX_SESSIONS_PER_USER = original_limit

    def test_revoke_all_user_sessions(self, sync_db_session: Session):
        """Test revoking all user sessions."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            username="testuser",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        # Create multiple sessions
        token1 = create_refresh_token()
        token2 = create_refresh_token()
        db_token1 = crud_create_refresh_token(
            sync_db_session, uuid.UUID(str(user.id)), token1
        )
        db_token2 = crud_create_refresh_token(
            sync_db_session, uuid.UUID(str(user.id)), token2
        )

        # Revoke all sessions except one
        revoked_count = revoke_all_user_sessions(
            sync_db_session, uuid.UUID(str(user.id)), uuid.UUID(str(db_token1.id))
        )
        assert revoked_count == 1

        # Check that one session is revoked
        sync_db_session.refresh(db_token2)
        assert db_token2.is_revoked is True

        # Check that the excepted session is still active
        sync_db_session.refresh(db_token1)
        assert db_token1.is_revoked is False


@pytest.mark.skip(
    reason="Requires complex refresh token functionality - not implemented yet"
)
class TestRefreshTokenService:
    """Test refresh token service functions."""

    def test_get_device_info(self):
        """Test device info extraction."""
        # Test Chrome on Windows
        request = Mock()
        request.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        device_info = get_device_info(request)
        assert device_info == "Chrome on Windows"

        # Test Firefox on macOS
        request.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0"
        }
        device_info = get_device_info(request)
        assert device_info == "Firefox on macOS"

        # Test unknown device
        request.headers = {"user-agent": "Unknown"}
        device_info = get_device_info(request)
        assert device_info == "Unknown Device"

    def test_get_client_ip(self):
        """Test client IP extraction."""
        request = Mock()

        # Test x-forwarded-for header
        request.headers = {"x-forwarded-for": "192.168.1.1, 10.0.0.1"}
        request.client = None
        ip = get_client_ip(request)
        assert ip == "192.168.1.1"

        # Test x-real-ip header
        request.headers = {"x-real-ip": "203.0.113.1"}
        ip = get_client_ip(request)
        assert ip == "203.0.113.1"

        # Test direct client
        request.headers = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        ip = get_client_ip(request)
        assert ip == "127.0.0.1"

        # Test no client info
        request.client = None
        ip = get_client_ip(request)
        assert ip == "unknown"

    def test_cookie_functions(self):
        """Test cookie management functions."""
        response = Mock()
        request = Mock()

        # Test setting cookie
        token = create_refresh_token()
        set_refresh_token_cookie(response, token)
        response.set_cookie.assert_called_once()

        # Test clearing cookie
        clear_refresh_token_cookie(response)
        response.delete_cookie.assert_called_once()

        # Test getting token from cookie
        request.cookies = {settings.REFRESH_TOKEN_COOKIE_NAME: token}
        retrieved_token = get_refresh_token_from_cookie(request)
        assert retrieved_token == token

        # Test no cookie
        request.cookies = {}
        retrieved_token = get_refresh_token_from_cookie(request)
        assert retrieved_token is None

    def test_create_user_session(self, sync_db_session: Session):
        """Test creating a user session."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            username="testuser",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        request = Mock()
        request.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124"
        }
        request.client = Mock()
        request.client.host = "127.0.0.1"

        access_token, refresh_token = create_user_session(
            sync_db_session, user, request
        )

        assert access_token is not None
        assert refresh_token is not None
        assert len(refresh_token) == 43

        # Verify token is stored in database
        db_token = verify_refresh_token_in_db(sync_db_session, refresh_token)
        assert db_token is not None
        assert db_token.user_id == user.id

    def test_refresh_access_token(self, sync_db_session: Session):
        """Test refreshing an access token."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            username="testuser",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        # Create a session
        token = create_refresh_token()
        crud_create_refresh_token(sync_db_session, uuid.UUID(str(user.id)), token)

        # Refresh access token
        result = refresh_access_token(sync_db_session, token)
        assert result is not None

        access_token, expires_at = result
        assert access_token is not None
        assert expires_at > datetime.utcnow()

        # Test invalid token
        result = refresh_access_token(sync_db_session, "invalid_token")
        assert result is None

    def test_revoke_session(self, sync_db_session: Session):
        """Test revoking a session."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            username="testuser",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        # Create a session
        token = create_refresh_token()
        crud_create_refresh_token(sync_db_session, uuid.UUID(str(user.id)), token)

        # Revoke session
        success = revoke_session(sync_db_session, token)
        assert success is True

        # Verify token is no longer valid
        result = verify_refresh_token_in_db(sync_db_session, token)
        assert result is None

    @pytest.mark.refresh_token
    def test_revoke_all_sessions(self, sync_db_session: Session):
        """Test revoking all sessions for a user."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            username="testuser",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        # Create multiple sessions
        token1 = create_refresh_token()
        token2 = create_refresh_token()
        crud_create_refresh_token(sync_db_session, uuid.UUID(str(user.id)), token1)
        crud_create_refresh_token(sync_db_session, uuid.UUID(str(user.id)), token2)

        # Revoke all sessions except one
        revoked_count = revoke_all_sessions(
            sync_db_session, uuid.UUID(str(user.id)), token1
        )
        assert revoked_count == 1

        # Verify one token is still valid (current session)
        result1 = verify_refresh_token_in_db(sync_db_session, token1)
        assert result1 is not None

        # Verify other token is revoked
        result2 = verify_refresh_token_in_db(sync_db_session, token2)
        assert result2 is None


@pytest.mark.skip(
    reason="Requires complex refresh token functionality - not implemented yet"
)
class TestRefreshTokenAPI:
    """Test refresh token API endpoints."""

    def test_refresh_token_endpoint_success(self, client, sync_db_session: Session):
        """Test successful token refresh."""
        # Create user and session
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            username="testuser",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        # Create session and get refresh token
        token = create_refresh_token()
        crud_create_refresh_token(sync_db_session, uuid.UUID(str(user.id)), token)

        # Make request with refresh token cookie
        response = client.post(
            "/api/v1/auth/refresh", cookies={settings.REFRESH_TOKEN_COOKIE_NAME: token}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert data["expires_in"] > 0

    def test_refresh_token_endpoint_no_cookie(self, client):
        """Test token refresh without cookie."""
        response = client.post("/api/v1/auth/refresh")

        assert response.status_code == 401
        data = response.json()
        assert "No refresh token provided" in data["detail"]

    def test_refresh_token_endpoint_invalid_token(self, client):
        """Test token refresh with invalid token."""
        response = client.post(
            "/api/v1/auth/refresh",
            cookies={settings.REFRESH_TOKEN_COOKIE_NAME: "invalid_token"},
        )

        assert response.status_code == 401
        data = response.json()
        assert "Invalid refresh token" in data["detail"]

    def test_logout_endpoint_success(self, client, sync_db_session: Session):
        """Test successful logout."""
        # Create user and session
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            username="testuser",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        # Create session and get refresh token
        token = create_refresh_token()
        crud_create_refresh_token(sync_db_session, uuid.UUID(str(user.id)), token)

        # Make logout request
        response = client.post(
            "/api/v1/auth/logout", cookies={settings.REFRESH_TOKEN_COOKIE_NAME: token}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully logged out"

        # Verify token is revoked
        result = verify_refresh_token_in_db(sync_db_session, token)
        assert result is None

    def test_logout_endpoint_no_cookie(self, client):
        """Test logout without cookie."""
        response = client.post("/api/v1/auth/logout")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully logged out"

    def test_get_user_sessions_endpoint(self, client, sync_db_session: Session):
        """Test getting user sessions."""
        # Create user and login
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            username="testuser",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        # Create session and get access token
        token = create_refresh_token()
        db_refresh_token = crud_create_refresh_token(
            sync_db_session, uuid.UUID(str(user.id)), token
        )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        from app.core.security import create_access_token

        access_token = create_access_token(
            subject=user.email, expires_delta=access_token_expires
        )

        # Make request with access token
        response = client.get(
            "/api/v1/auth/sessions",
            headers={"Authorization": f"Bearer {access_token}"},
            cookies={settings.REFRESH_TOKEN_COOKIE_NAME: token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert "total_sessions" in data
        assert data["total_sessions"] == 1
        assert len(data["sessions"]) == 1

        session = data["sessions"][0]
        assert session["id"] == str(db_refresh_token.id)
        assert session["is_current"] is True

    def test_revoke_session_endpoint(self, client, sync_db_session: Session):
        """Test revoking a specific session."""
        # Create user and login
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            username="testuser",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        # Create session and get access token
        token = create_refresh_token()
        db_refresh_token = crud_create_refresh_token(
            sync_db_session, uuid.UUID(str(user.id)), token
        )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        from app.core.security import create_access_token

        access_token = create_access_token(
            subject=user.email, expires_delta=access_token_expires
        )

        # Make request to revoke session
        response = client.delete(
            f"/api/v1/auth/sessions/{db_refresh_token.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Session revoked successfully"

        # Verify session is revoked
        result = verify_refresh_token_in_db(sync_db_session, token)
        assert result is None

    @pytest.mark.refresh_token
    def test_revoke_all_sessions_endpoint(self, client, sync_db_session: Session):
        """Test revoking all sessions."""
        # Create user and login
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            username="testuser",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        # Create multiple sessions
        token1 = create_refresh_token()
        token2 = create_refresh_token()
        crud_create_refresh_token(sync_db_session, uuid.UUID(str(user.id)), token1)
        crud_create_refresh_token(sync_db_session, uuid.UUID(str(user.id)), token2)

        # Get access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        from app.core.security import create_access_token

        access_token = create_access_token(
            subject=user.email, expires_delta=access_token_expires
        )

        # Make request to revoke all sessions except current
        response = client.delete(
            "/api/v1/auth/sessions",
            headers={"Authorization": f"Bearer {access_token}"},
            cookies={settings.REFRESH_TOKEN_COOKIE_NAME: token1},
        )

        assert response.status_code == 200
        data = response.json()
        assert "Successfully revoked 1 sessions" in data["message"]
        assert data["revoked_count"] == 1

        # Verify one token is still valid (current session)
        result1 = verify_refresh_token_in_db(sync_db_session, token1)
        assert result1 is not None

        # Verify other token is revoked
        result2 = verify_refresh_token_in_db(sync_db_session, token2)
        assert result2 is None
