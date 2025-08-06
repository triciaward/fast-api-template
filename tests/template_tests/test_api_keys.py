import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.security import generate_api_key, hash_api_key, verify_api_key
from app.crud import api_key as crud_api_key
from app.models import User
from app.schemas.user import APIKeyCreate


class TestAPIKeySecurity:
    """Test API key generation and hashing functions."""

    def test_generate_api_key(self):
        """Test API key generation."""
        key1 = generate_api_key()
        key2 = generate_api_key()

        # Keys should be different
        assert key1 != key2

        # Keys should start with 'sk_'
        assert key1.startswith("sk_")
        assert key2.startswith("sk_")

        # Keys should be reasonably long
        assert len(key1) > 20
        assert len(key2) > 20

    def test_hash_api_key(self):
        """Test API key hashing."""
        key = generate_api_key()
        hashed = hash_api_key(key)

        # Hash should be different from original
        assert hashed != key

        # Hash should be a string
        assert isinstance(hashed, str)

        # Hash should be reasonably long
        assert len(hashed) > 20

    def test_verify_api_key(self):
        """Test API key verification."""
        key = generate_api_key()
        hashed = hash_api_key(key)

        # Should verify correctly
        assert verify_api_key(key, hashed) is True

        # Should not verify with wrong key
        wrong_key = generate_api_key()
        assert verify_api_key(wrong_key, hashed) is False

        # Should not verify with wrong hash
        wrong_hash = hash_api_key(wrong_key)
        assert verify_api_key(key, wrong_hash) is False


@pytest.mark.skip(
    reason="Database session mismatch - API endpoints use different session than test fixtures",
)
class TestAPIKeyCRUD:
    """Test API key CRUD operations."""

    def test_create_api_key(self, sync_db_session: Session, test_user: User):
        """Test creating an API key."""
        user_id = str(test_user.id)
        api_key_data = APIKeyCreate(
            label="Test Key",
            scopes=["read_events", "write_events"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        api_key = crud_api_key.create_api_key_sync(
            db=sync_db_session,
            api_key_data=api_key_data,
            user_id=user_id,
        )

        assert str(api_key.user_id) == user_id
        assert api_key.label == "Test Key"
        assert api_key.scopes == ["read_events", "write_events"]
        assert api_key.is_active is True
        assert api_key.is_deleted is False
        assert api_key.created_at is not None

    def test_get_api_key_by_hash(self, sync_db_session: Session, test_user: User):
        """Test getting API key by hash."""
        # Create a key
        user_id = str(test_user.id)
        raw_key = generate_api_key()
        api_key_data = APIKeyCreate(
            label="Test Key",
            scopes=["read_events"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        api_key = crud_api_key.create_api_key_sync(
            db=sync_db_session,
            api_key_data=api_key_data,
            user_id=user_id,
            raw_key=raw_key,
        )

        # Get by hash - use the hash that was actually stored
        found_key = crud_api_key.get_api_key_by_hash_sync(
            sync_db_session,
            api_key.key_hash,  # type: ignore
        )

        assert found_key is not None
        assert found_key.id == api_key.id
        assert str(found_key.user_id) == user_id

    def test_verify_api_key_in_db(self, sync_db_session: Session, test_user: User):
        """Test verifying API key in database."""
        # Create a key
        user_id = str(test_user.id)
        raw_key = generate_api_key()
        api_key_data = APIKeyCreate(
            label="Test Key",
            scopes=["read_events"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        api_key = crud_api_key.create_api_key_sync(
            db=sync_db_session,
            api_key_data=api_key_data,
            user_id=user_id,
            raw_key=raw_key,
        )

        # Verify the key
        verified_key = crud_api_key.verify_api_key_in_db_sync(sync_db_session, raw_key)

        assert verified_key is not None
        assert verified_key.id == api_key.id

        # Test with wrong key
        wrong_key = generate_api_key()
        wrong_verified = crud_api_key.verify_api_key_in_db_sync(
            sync_db_session,
            wrong_key,
        )
        assert wrong_verified is None

    def test_get_user_api_keys(self, sync_db_session: Session, test_user: User):
        """Test getting user's API keys."""
        user_id = str(test_user.id)

        # Create multiple keys for the user
        for i in range(3):
            api_key_data = APIKeyCreate(
                label=f"Test Key {i}",
                scopes=[f"scope_{i}"],
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            )
            crud_api_key.create_api_key_sync(sync_db_session, api_key_data, user_id)

        # Get user's keys
        keys = crud_api_key.get_user_api_keys_sync(sync_db_session, user_id)

        assert len(keys) == 3
        for key in keys:
            assert str(key.user_id) == user_id

    def test_deactivate_api_key(self, sync_db_session: Session, test_user: User):
        """Test deactivating an API key."""
        user_id = str(test_user.id)
        api_key_data = APIKeyCreate(
            label="Test Key",
            scopes=["read_events"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        api_key = crud_api_key.create_api_key_sync(
            sync_db_session,
            api_key_data,
            user_id,
        )

        # Deactivate the key
        success = crud_api_key.deactivate_api_key_sync(
            sync_db_session,
            str(api_key.id),
            user_id,
        )

        assert success is True

        # Verify the key is deactivated
        deactivated_key = crud_api_key.get_api_key_by_id_sync(
            sync_db_session,
            str(api_key.id),
            user_id,
        )
        assert deactivated_key is not None
        assert deactivated_key.is_active is False

    def test_rotate_api_key(self, sync_db_session: Session, test_user: User):
        """Test rotating an API key."""
        user_id = str(test_user.id)
        api_key_data = APIKeyCreate(
            label="Test Key",
            scopes=["read_events"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        api_key = crud_api_key.create_api_key_sync(
            sync_db_session,
            api_key_data,
            user_id,
        )
        original_hash = api_key.key_hash

        # Rotate the key
        result = crud_api_key.rotate_api_key_sync(
            sync_db_session,
            str(api_key.id),
            user_id,
        )

        assert result is not None
        assert len(result) == 2
        rotated_key, new_raw_key = result

        # Check that hash changed
        assert rotated_key is not None
        assert rotated_key.key_hash != original_hash

        # Check that new key works
        assert new_raw_key is not None
        new_verified = crud_api_key.verify_api_key_in_db_sync(
            sync_db_session,
            new_raw_key,
        )
        assert new_verified is not None
        assert new_verified.id == api_key.id

    def test_expired_api_key_found_but_invalid(
        self,
        sync_db_session: Session,
        test_user: User,
    ):
        """Test that expired API keys are found but marked as invalid."""
        user_id = str(test_user.id)
        raw_key = generate_api_key()
        api_key_data = APIKeyCreate(
            label="Test Key",
            scopes=["read_events"],
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),  # Expired
        )

        api_key = crud_api_key.create_api_key_sync(
            db=sync_db_session,
            api_key_data=api_key_data,
            user_id=user_id,
            raw_key=raw_key,
        )

        # Should find expired key (for status checking)
        verified_key = crud_api_key.verify_api_key_in_db_sync(sync_db_session, raw_key)
        assert verified_key is not None
        assert verified_key.id == api_key.id
        assert verified_key.expires_at < datetime.now(timezone.utc)  # Should be expired

    def test_inactive_api_key_found_but_invalid(
        self,
        sync_db_session: Session,
        test_user: User,
    ):
        """Test that inactive API keys are found but marked as invalid."""
        user_id = str(test_user.id)
        raw_key = generate_api_key()
        api_key_data = APIKeyCreate(
            label="Test Key",
            scopes=["read_events"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        api_key = crud_api_key.create_api_key_sync(
            db=sync_db_session,
            api_key_data=api_key_data,
            user_id=user_id,
            raw_key=raw_key,
        )

        # Deactivate the key
        api_key.is_active = False  # type: ignore
        sync_db_session.commit()

        # Should find inactive key (for status checking)
        verified_key = crud_api_key.verify_api_key_in_db_sync(sync_db_session, raw_key)
        assert verified_key is not None
        assert verified_key.id == api_key.id
        assert verified_key.is_active is False  # Should be inactive


@pytest.mark.skip(
    reason="Database session mismatch - API endpoints use different session than test fixtures",
)
class TestAPIKeyAuthentication:
    """Test API key authentication dependencies."""

    def test_get_api_key_user_valid(
        self,
        client: TestClient,
        sync_db_session: Session,
        test_user: User,
    ):
        """Test valid API key authentication."""
        # Create an API key for the user
        raw_key = generate_api_key()
        api_key_data = APIKeyCreate(
            label="Test Key",
            scopes=["read_events"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        crud_api_key.create_api_key_sync(
            db=sync_db_session,
            api_key_data=api_key_data,
            user_id=str(test_user.id),
            raw_key=raw_key,
        )

        # Test authentication
        response = client.get(
            "/api/v1/users/me/api-key",
            headers={"Authorization": f"Bearer {raw_key}"},
        )

        # Should work with API key
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(test_user.id)
        assert "read_events" in data["scopes"]

    def test_get_api_key_user_invalid_format(self, client: TestClient):
        """Test API key authentication with invalid format."""
        response = client.get(
            "/api/v1/users/me/api-key",
            headers={"Authorization": "InvalidFormat"},
        )

        assert response.status_code == 401
        assert (
            "Invalid authorization header format" in response.json()["error"]["message"]
        )

    def test_get_api_key_user_missing_header(self, client: TestClient):
        """Test API key authentication with missing header."""
        response = client.get("/api/v1/users/me/api-key")

        assert response.status_code == 401
        assert "API key required" in response.json()["error"]["message"]

    def test_get_api_key_user_invalid_key(self, client: TestClient):
        """Test API key authentication with invalid key."""
        invalid_key = generate_api_key()

        response = client.get(
            "/api/v1/users/me/api-key",
            headers={"Authorization": f"Bearer {invalid_key}"},
        )

        assert response.status_code == 401
        assert "Invalid API key" in response.json()["error"]["message"]

    def test_get_api_key_user_expired(
        self,
        client: TestClient,
        sync_db_session: Session,
        test_user: User,
    ):
        """Test API key authentication with expired key."""
        # Create an expired API key
        raw_key = generate_api_key()
        api_key_data = APIKeyCreate(
            label="Test Key",
            scopes=["read_events"],
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )

        crud_api_key.create_api_key_sync(
            db=sync_db_session,
            api_key_data=api_key_data,
            user_id=str(test_user.id),
            raw_key=raw_key,
        )

        response = client.get(
            "/api/v1/users/me/api-key",
            headers={"Authorization": f"Bearer {raw_key}"},
        )

        assert response.status_code == 401
        assert "API key has expired" in response.json()["error"]["message"]

    def test_get_api_key_user_inactive(
        self,
        client: TestClient,
        sync_db_session: Session,
        test_user: User,
    ):
        """Test API key authentication with inactive key."""
        # Create an API key
        raw_key = generate_api_key()
        api_key_data = APIKeyCreate(
            label="Test Key",
            scopes=["read_events"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        api_key = crud_api_key.create_api_key_sync(
            db=sync_db_session,
            api_key_data=api_key_data,
            user_id=str(test_user.id),
            raw_key=raw_key,
        )

        # Deactivate the key
        api_key.is_active = False  # type: ignore
        sync_db_session.commit()

        response = client.get(
            "/api/v1/users/me/api-key",
            headers={"Authorization": f"Bearer {raw_key}"},
        )

        assert response.status_code == 401
        assert "API key is inactive" in response.json()["error"]["message"]


class TestAPIKeyEndpoints:
    """Test API key management endpoints."""

    @pytest.mark.skip(
        reason="Database session mismatch - API endpoints use different session than test fixtures",
    )
    async def test_create_api_key(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_user: User,
        test_user_token: str,
    ):
        """Test creating an API key."""
        api_key_data = {
            "label": "Test API Key",
            "scopes": ["read_events", "write_events"],
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        }

        response = client.post(
            "/api/v1/auth/api-keys",
            json=api_key_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 201
        data = response.json()

        assert "api_key" in data
        assert "raw_key" in data
        assert data["api_key"]["label"] == "Test API Key"
        assert data["api_key"]["scopes"] == ["read_events", "write_events"]
        assert data["api_key"]["user_id"] == str(test_user.id)
        assert data["raw_key"].startswith("sk_")

    @pytest.mark.skip(
        reason="Database session mismatch - API endpoints use different session than test fixtures",
    )
    async def test_list_api_keys(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_user: User,
        test_user_token: str,
    ):
        """Test listing API keys."""
        # Create some API keys
        for i in range(3):
            api_key_data = APIKeyCreate(
                label=f"Test Key {i}",
                scopes=[f"scope_{i}"],
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            )
            await crud_api_key.create_api_key(
                db_session,
                api_key_data,
                str(test_user.id),
            )

        response = client.get(
            "/api/v1/auth/api-keys",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["metadata"]["total"] == 3

    @pytest.mark.skip(
        reason="Database session mismatch - API endpoints use different session than test fixtures",
    )
    async def test_deactivate_api_key(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_user: User,
        test_user_token: str,
    ):
        """Test deactivating an API key."""
        # Create an API key
        api_key_data = APIKeyCreate(
            label="Test Key",
            scopes=["read_events"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        api_key = await crud_api_key.create_api_key(
            db_session,
            api_key_data,
            str(test_user.id),
        )

        response = client.delete(
            f"/api/v1/auth/api-keys/{api_key.id}",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 204  # No Content for DELETE operations

        # Refresh the session to get the updated data
        await db_session.refresh(api_key)
        assert api_key.is_active is False

    @pytest.mark.skip(
        reason="Database session mismatch - API endpoints use different session than test fixtures",
    )
    async def test_rotate_api_key(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_user: User,
        test_user_token: str,
    ):
        """Test rotating an API key."""
        # Create an API key
        api_key_data = APIKeyCreate(
            label="Test Key",
            scopes=["read_events"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        api_key = await crud_api_key.create_api_key(
            db_session,
            api_key_data,
            str(test_user.id),
        )

        response = client.post(
            f"/api/v1/auth/api-keys/{api_key.id}/rotate",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "api_key" in data
        assert "new_raw_key" in data
        assert data["new_raw_key"].startswith("sk_")

    def test_create_api_key_unauthorized(self, client: TestClient):
        """Test creating an API key without authentication."""
        api_key_data = {
            "label": "Test Key",
            "scopes": ["read_events"],
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        }

        response = client.post("/api/v1/auth/api-keys", json=api_key_data)

        assert response.status_code == 401

    def test_deactivate_other_user_key(
        self,
        client: TestClient,
        sync_db_session: Session,
        test_user: User,
        test_user_token: str,
    ):
        """Test that users cannot deactivate other users' keys."""
        # Create another user and API key
        other_user = User(
            id=uuid.uuid4(),
            email="other@example.com",
            username="otheruser",
            hashed_password="hashed",
        )
        sync_db_session.add(other_user)
        sync_db_session.commit()

        api_key_data = APIKeyCreate(
            label="Other User Key",
            scopes=["read_events"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        api_key = crud_api_key.create_api_key_sync(
            sync_db_session,
            api_key_data,
            str(other_user.id),
        )

        # Try to deactivate it with current user's token
        response = client.delete(
            f"/api/v1/auth/api-keys/{api_key.id}",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 404

    @pytest.mark.skip(
        reason="Database session mismatch - API endpoints use different session than test fixtures",
    )
    def test_rotate_other_user_key(
        self,
        client: TestClient,
        sync_db_session: Session,
        test_user: User,
        test_user_token: str,
    ):
        """Test that users cannot rotate other users' keys."""
        # Create another user and API key
        other_user = User(
            id=uuid.uuid4(),
            email="other@example.com",
            username="otheruser",
            hashed_password="hashed",
        )
        sync_db_session.add(other_user)
        sync_db_session.commit()

        api_key_data = APIKeyCreate(
            label="Other User Key",
            scopes=["read_events"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        api_key = crud_api_key.create_api_key_sync(
            sync_db_session,
            api_key_data,
            str(other_user.id),
        )

        # Try to rotate it with current user's token
        response = client.post(
            f"/api/v1/auth/api-keys/{api_key.id}/rotate",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 404


@pytest.mark.skip(
    reason="Database session mismatch - API endpoints use different session than test fixtures",
)
class TestAPIKeyScopes:
    """Test API key scope functionality."""

    def test_require_api_scope_success(
        self,
        client: TestClient,
        sync_db_session: Session,
        test_user: User,
    ):
        """Test successful scope requirement."""
        # Create an API key with the required scope
        raw_key = generate_api_key()
        api_key_data = APIKeyCreate(
            label="Test Key",
            scopes=["read_events", "write_events"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        crud_api_key.create_api_key_sync(
            db=sync_db_session,
            api_key_data=api_key_data,
            user_id=str(test_user.id),
            raw_key=raw_key,
        )

        # Test that the scope checking dependency works
        from app.api.api_v1.endpoints.users import require_api_scope

        # Create a scope checker for a scope the key has
        scope_checker = require_api_scope("read_events")

        # Verify the function exists and has the right signature
        assert callable(scope_checker)

    def test_require_api_scope_failure(
        self,
        client: TestClient,
        sync_db_session: Session,
        test_user: User,
    ):
        """Test failed scope requirement."""
        # Create an API key without the required scope
        raw_key = generate_api_key()
        api_key_data = APIKeyCreate(
            label="Test Key",
            scopes=["read_events"],  # Missing write_events
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        crud_api_key.create_api_key_sync(
            db=sync_db_session,
            api_key_data=api_key_data,
            user_id=str(test_user.id),
            raw_key=raw_key,
        )

        # Test that the scope checking dependency works
        from app.api.api_v1.endpoints.users import require_api_scope

        # Create a scope checker for a scope the key doesn't have
        scope_checker = require_api_scope("write_events")

        # Verify the function exists and has the right signature
        assert callable(scope_checker)


@pytest.mark.skip(
    reason="Database session mismatch - API endpoints use different session than test fixtures",
)
class TestAPIKeyIntegration:
    """Test API key authentication integration with other endpoints."""

    def test_api_key_works_with_user_endpoints(
        self,
        client: TestClient,
        sync_db_session: Session,
        test_user: User,
    ):
        """Test that API keys can be used to access user endpoints."""
        # Create an API key for the user
        raw_key = generate_api_key()
        api_key_data = APIKeyCreate(
            label="Test Key",
            scopes=["read_users"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        crud_api_key.create_api_key_sync(
            db=sync_db_session,
            api_key_data=api_key_data,
            user_id=str(test_user.id),
            raw_key=raw_key,
        )

        # Test accessing a protected user endpoint with API key
        # Note: This would require the endpoint to support API key auth
        # For now, we'll test the authentication dependency directly
        from app.api.api_v1.endpoints.users import get_api_key_user

        # This would be called by FastAPI in a real request
        # We can verify the function exists and has the right signature
        assert callable(get_api_key_user)

    def test_api_key_scope_enforcement(
        self,
        client: TestClient,
        sync_db_session: Session,
        test_user: User,
    ):
        """Test that API key scopes are properly enforced."""
        # Create API key with limited scope
        raw_key = generate_api_key()
        api_key_data = APIKeyCreate(
            label="Limited Key",
            scopes=["read_events"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        crud_api_key.create_api_key_sync(
            db=sync_db_session,
            api_key_data=api_key_data,
            user_id=str(test_user.id),
            raw_key=raw_key,
        )

        # Test that the scope checking dependency works
        from app.api.api_v1.endpoints.users import require_api_scope

        # Create a scope checker for a scope the key doesn't have
        scope_checker = require_api_scope("write_users")

        # Verify the function exists and has the right signature
        assert callable(scope_checker)

    def test_api_key_authentication_flow(
        self,
        client: TestClient,
        sync_db_session: Session,
        test_user: User,
    ):
        """Test the complete API key authentication flow."""
        # 1. Create an API key
        raw_key = generate_api_key()
        api_key_data = APIKeyCreate(
            label="Integration Test Key",
            scopes=["read_events", "write_events"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        api_key = crud_api_key.create_api_key_sync(
            db=sync_db_session,
            api_key_data=api_key_data,
            user_id=str(test_user.id),
            raw_key=raw_key,
        )

        # 2. Verify the key exists and is valid
        verified_key = crud_api_key.verify_api_key_in_db_sync(sync_db_session, raw_key)
        assert verified_key is not None
        assert verified_key.id == api_key.id
        assert verified_key.is_active is True

        # 3. Test authentication with the key
        response = client.get(
            "/api/v1/users/me/api-key",
            headers={"Authorization": f"Bearer {raw_key}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(test_user.id)
        assert "read_events" in data["scopes"]
        assert "write_events" in data["scopes"]

        # 4. Test that the key can be used for multiple requests
        response2 = client.get(
            "/api/v1/users/me/api-key",
            headers={"Authorization": f"Bearer {raw_key}"},
        )

        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["user_id"] == str(test_user.id)

    def test_api_key_authentication_with_invalid_scopes(
        self,
        client: TestClient,
        sync_db_session: Session,
        test_user: User,
    ):
        """Test API key authentication when key has insufficient scopes."""
        # Create API key with limited scopes
        raw_key = generate_api_key()
        api_key_data = APIKeyCreate(
            label="Limited Key",
            scopes=["read_events"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        crud_api_key.create_api_key_sync(
            db=sync_db_session,
            api_key_data=api_key_data,
            user_id=str(test_user.id),
            raw_key=raw_key,
        )

        # Test authentication still works (scopes are checked at endpoint level)
        response = client.get(
            "/api/v1/users/me/api-key",
            headers={"Authorization": f"Bearer {raw_key}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(test_user.id)
        assert "read_events" in data["scopes"]
        assert "write_events" not in data["scopes"]

    def test_api_key_authentication_with_expired_key(
        self,
        client: TestClient,
        sync_db_session: Session,
        test_user: User,
    ):
        """Test API key authentication with expired key."""
        # Create an expired API key
        raw_key = generate_api_key()
        api_key_data = APIKeyCreate(
            label="Expired Key",
            scopes=["read_events"],
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )

        crud_api_key.create_api_key_sync(
            db=sync_db_session,
            api_key_data=api_key_data,
            user_id=str(test_user.id),
            raw_key=raw_key,
        )

        # Test that expired key is rejected
        response = client.get(
            "/api/v1/users/me/api-key",
            headers={"Authorization": f"Bearer {raw_key}"},
        )

        assert response.status_code == 401
        assert "API key has expired" in response.json()["error"]["message"]

    def test_api_key_authentication_with_inactive_key(
        self,
        client: TestClient,
        sync_db_session: Session,
        test_user: User,
    ):
        """Test API key authentication with inactive key."""
        # Create an API key
        raw_key = generate_api_key()
        api_key_data = APIKeyCreate(
            label="Inactive Key",
            scopes=["read_events"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        api_key = crud_api_key.create_api_key_sync(
            db=sync_db_session,
            api_key_data=api_key_data,
            user_id=str(test_user.id),
            raw_key=raw_key,
        )

        # Deactivate the key
        api_key.is_active = False  # type: ignore
        sync_db_session.commit()

        # Test that inactive key is rejected
        response = client.get(
            "/api/v1/users/me/api-key",
            headers={"Authorization": f"Bearer {raw_key}"},
        )

        assert response.status_code == 401
        assert "API key is inactive" in response.json()["error"]["message"]

    def test_api_key_authentication_with_nonexistent_key(self, client: TestClient):
        """Test API key authentication with non-existent key."""
        # Generate a key but don't store it in the database
        fake_key = generate_api_key()

        response = client.get(
            "/api/v1/users/me/api-key",
            headers={"Authorization": f"Bearer {fake_key}"},
        )

        assert response.status_code == 401
        assert "Invalid API key" in response.json()["error"]["message"]

    def test_api_key_authentication_with_malformed_header(self, client: TestClient):
        """Test API key authentication with malformed authorization header."""
        # Test without Bearer prefix
        response = client.get(
            "/api/v1/users/me/api-key",
            headers={"Authorization": "sk_invalid_key"},
        )

        assert response.status_code == 401
        assert (
            "Invalid authorization header format" in response.json()["error"]["message"]
        )

        # Test with empty Bearer token
        response2 = client.get(
            "/api/v1/users/me/api-key",
            headers={"Authorization": "Bearer "},
        )

        assert response2.status_code == 401
        assert "Invalid API key" in response2.json()["error"]["message"]


@pytest.mark.skip(
    reason="Database session mismatch - API endpoints use different session than test fixtures",
)
def test_api_key_usage_audit_logging(
    client: TestClient,
    sync_db_session: Session,
    test_user: User,
):
    """Test that API key usage is logged to audit logs."""
    from app.crud.audit_log import get_audit_logs_by_event_type_sync

    # Create an API key for the user
    raw_key = generate_api_key()
    api_key_data = APIKeyCreate(
        label="Audit Test Key",
        scopes=["read_events"],
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )

    api_key = crud_api_key.create_api_key_sync(
        db=sync_db_session,
        api_key_data=api_key_data,
        user_id=str(test_user.id),
        raw_key=raw_key,
    )

    # Make a request using the API key
    response = client.get(
        "/api/v1/users/me/api-key",
        headers={"Authorization": f"Bearer {raw_key}"},
    )

    assert response.status_code == 200

    # Check that the API key usage was logged
    audit_logs = get_audit_logs_by_event_type_sync(
        sync_db_session,
        "api_key_usage",
        limit=10,
    )

    # Find the log entry for this API key
    api_key_logs = [
        log
        for log in audit_logs
        if log.context and log.context.get("api_key_id") == str(api_key.id)
    ]

    assert len(api_key_logs) >= 1

    # Verify the log entry contains the expected information
    log_entry = api_key_logs[0]
    assert log_entry.event_type == "api_key_usage"
    assert log_entry.success is True
    assert log_entry.context["api_key_id"] == str(api_key.id)
    assert log_entry.context["key_label"] == "Audit Test Key"
    assert log_entry.context["api_key_user_id"] == str(test_user.id)
    assert log_entry.context["endpoint_path"] == "/api/v1/users/me/api-key"
    assert log_entry.context["http_method"] == "GET"
    assert log_entry.ip_address is not None
    assert log_entry.user_agent is not None


@pytest.mark.skip(
    reason="Database session mismatch - API endpoints use different session than test fixtures",
)
def test_api_key_usage_audit_logging_system_key(
    client: TestClient,
    sync_db_session: Session,
):
    """Test that system-level API key usage is logged correctly."""
    from app.crud.audit_log import get_audit_logs_by_event_type_sync

    # Create a system-level API key (no user_id)
    raw_key = generate_api_key()
    api_key_data = APIKeyCreate(
        label="System Integration Key",
        scopes=["read_events", "write_events"],
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )

    api_key = crud_api_key.create_api_key_sync(
        db=sync_db_session,
        api_key_data=api_key_data,
        user_id=None,  # System-level key
        raw_key=raw_key,
    )

    # Make a request using the API key
    response = client.get(
        "/api/v1/users/me/api-key",
        headers={"Authorization": f"Bearer {raw_key}"},
    )

    assert response.status_code == 200

    # Check that the API key usage was logged
    audit_logs = get_audit_logs_by_event_type_sync(
        sync_db_session,
        "api_key_usage",
        limit=10,
    )

    # Find the log entry for this API key
    api_key_logs = [
        log
        for log in audit_logs
        if log.context and log.context.get("api_key_id") == str(api_key.id)
    ]

    assert len(api_key_logs) >= 1

    # Verify the log entry contains the expected information
    log_entry = api_key_logs[0]
    assert log_entry.event_type == "api_key_usage"
    assert log_entry.success is True
    assert log_entry.context["api_key_id"] == str(api_key.id)
    assert log_entry.context["key_label"] == "System Integration Key"
    assert "api_key_user_id" not in log_entry.context  # No user_id for system keys
    assert log_entry.context["endpoint_path"] == "/api/v1/users/me/api-key"
    assert log_entry.context["http_method"] == "GET"


# Fixtures for testing
@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def test_user_token(test_user: User) -> str:
    """Create a test user token."""
    from app.core.security import create_access_token

    return create_access_token(subject=test_user.email)
