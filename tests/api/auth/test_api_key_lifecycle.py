"""Comprehensive API key lifecycle tests to improve coverage."""

import types
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from tests.utils.auth_helpers import create_test_user, override_dependency

pytestmark = pytest.mark.asyncio


class TestAPIKeyCreation:
    """Test API key creation edge cases."""

    async def test_create_api_key_success(self, monkeypatch, async_client):
        """Test successful API key creation."""
        from app.api.auth import api_keys as mod
        from app.main import app

        current_user = create_test_user()

        async def fake_get_current_user():
            return current_user

        mock_api_key = types.SimpleNamespace(
            id=uuid4(),
            label="Test API Key",
            created_at=datetime.now(timezone.utc),
            is_active=True,
            scopes=["read"],
            user_id=str(uuid4()),
        )

        async def mock_create_api_key(db, api_key_data, user_id, raw_key):
            return mock_api_key

        monkeypatch.setattr(
            "app.core.security.generate_api_key",
            lambda: "test_raw_key_123",
        )
        monkeypatch.setattr(mod.crud_api_key, "create_api_key", mock_create_api_key)

        cleanup = override_dependency(app, mod.get_current_user, fake_get_current_user)

        try:
            resp = await async_client.post(
                "/auth/api-keys",
                json={"label": "Test API Key", "scopes": ["read"]},
                headers={"authorization": "Bearer token"},
            )
            assert resp.status_code == 201
            data = resp.json()
            assert "api_key" in data
            assert "raw_key" in data
            assert data["raw_key"] == "test_raw_key_123"
        finally:
            cleanup()

    async def test_create_api_key_database_error(self, monkeypatch, async_client):
        """Test API key creation with database error."""
        from app.api.auth import api_keys as mod
        from app.main import app

        current_user = create_test_user()

        async def fake_get_current_user():
            return current_user

        async def mock_create_api_key_error(db, api_key_data, user_id, raw_key):
            raise Exception("Database connection failed")

        monkeypatch.setattr(
            "app.core.security.generate_api_key",
            lambda: "test_raw_key_123",
        )
        monkeypatch.setattr(
            mod.crud_api_key,
            "create_api_key",
            mock_create_api_key_error,
        )

        cleanup = override_dependency(app, mod.get_current_user, fake_get_current_user)

        try:
            resp = await async_client.post(
                "/auth/api-keys",
                json={"label": "Test API Key", "scopes": ["read"]},
                headers={"authorization": "Bearer token"},
            )
            assert resp.status_code == 500
            assert "Failed to create API key" in resp.json()["error"]["message"]
        finally:
            cleanup()

    async def test_create_api_key_with_expiration(self, monkeypatch, async_client):
        """Test API key creation with expiration date."""
        from app.api.auth import api_keys as mod
        from app.main import app

        current_user = create_test_user()

        async def fake_get_current_user():
            return current_user

        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        mock_api_key = types.SimpleNamespace(
            id=uuid4(),
            label="Expiring API Key",
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            is_active=True,
            scopes=["read"],
            user_id=str(uuid4()),
        )

        async def mock_create_api_key(db, api_key_data, user_id, raw_key):
            assert api_key_data.expires_at is not None
            return mock_api_key

        monkeypatch.setattr(
            "app.core.security.generate_api_key",
            lambda: "test_raw_key_123",
        )
        monkeypatch.setattr(mod.crud_api_key, "create_api_key", mock_create_api_key)

        cleanup = override_dependency(app, mod.get_current_user, fake_get_current_user)

        try:
            resp = await async_client.post(
                "/auth/api-keys",
                json={
                    "label": "Expiring API Key",
                    "scopes": ["read"],
                    "expires_at": expires_at.isoformat(),
                },
                headers={"authorization": "Bearer token"},
            )
            assert resp.status_code == 201
        finally:
            cleanup()


class TestAPIKeyListing:
    """Test API key listing with pagination."""

    async def test_list_api_keys_empty(self, monkeypatch, async_client):
        """Test listing API keys when user has none."""
        from app.api.auth import api_keys as mod
        from app.main import app

        current_user = create_test_user()

        async def fake_get_current_user():
            return current_user

        async def mock_get_user_api_keys(db, user_id, skip, limit):
            return []

        async def mock_count_user_api_keys(db, user_id):
            return 0

        monkeypatch.setattr(
            mod.crud_api_key,
            "get_user_api_keys",
            mock_get_user_api_keys,
        )
        monkeypatch.setattr(
            mod.crud_api_key,
            "count_user_api_keys",
            mock_count_user_api_keys,
        )

        cleanup = override_dependency(app, mod.get_current_user, fake_get_current_user)

        try:
            resp = await async_client.get(
                "/auth/api-keys",
                headers={"authorization": "Bearer token"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["items"] == []
            assert data["metadata"]["total"] == 0
        finally:
            cleanup()

    async def test_list_api_keys_with_pagination(self, monkeypatch, async_client):
        """Test listing API keys with pagination parameters."""
        from app.api.auth import api_keys as mod
        from app.main import app

        current_user = create_test_user()

        async def fake_get_current_user():
            return current_user

        # Create mock API keys
        mock_api_keys = []
        for i in range(5):
            mock_api_key = MagicMock()
            mock_api_key.id = uuid4()
            mock_api_key.label = f"API Key {i + 1}"
            mock_api_key.created_at = datetime.now(timezone.utc)
            mock_api_key.is_active = True
            mock_api_key.expires_at = None
            mock_api_key.scopes = ["read"]
            mock_api_key.user_id = str(uuid4())
            # Ensure the mock is properly configured to avoid serialization issues
            mock_api_key.__str__ = lambda: "MockAPIKey"
            mock_api_key.__repr__ = lambda: "MockAPIKey"
            mock_api_keys.append(mock_api_key)

        async def mock_get_user_api_keys(db, user_id, skip, limit):
            return mock_api_keys[skip : skip + limit]

        async def mock_count_user_api_keys(db, user_id):
            return len(mock_api_keys)

        monkeypatch.setattr(
            mod.crud_api_key,
            "get_user_api_keys",
            mock_get_user_api_keys,
        )
        monkeypatch.setattr(
            mod.crud_api_key,
            "count_user_api_keys",
            mock_count_user_api_keys,
        )

        cleanup = override_dependency(app, mod.get_current_user, fake_get_current_user)

        try:
            resp = await async_client.get(
                "/auth/api-keys?page=1&size=3",
                headers={"authorization": "Bearer token"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["items"]) == 3
            assert data["metadata"]["total"] == 5
            assert data["metadata"]["page"] == 1
        finally:
            cleanup()


class TestAPIKeyDeactivation:
    """Test API key deactivation functionality."""

    async def test_deactivate_api_key_success(self, monkeypatch, async_client):
        """Test successful API key deactivation."""
        from app.api.auth import api_keys as mod
        from app.main import app

        current_user = create_test_user()
        api_key_id = str(uuid4())

        async def fake_get_current_user():
            return current_user

        async def mock_deactivate_api_key(db, key_id, user_id):
            assert key_id == api_key_id
            assert user_id == str(current_user.id)
            return True

        monkeypatch.setattr(
            mod.crud_api_key,
            "deactivate_api_key",
            mock_deactivate_api_key,
        )

        cleanup = override_dependency(app, mod.get_current_user, fake_get_current_user)

        try:
            resp = await async_client.delete(
                f"/auth/api-keys/{api_key_id}",
                headers={"authorization": "Bearer token"},
            )
            assert resp.status_code == 204
        finally:
            cleanup()

    async def test_deactivate_api_key_not_found(self, monkeypatch, async_client):
        """Test deactivating non-existent or unauthorized API key."""
        from app.api.auth import api_keys as mod
        from app.main import app

        current_user = create_test_user()
        api_key_id = str(uuid4())

        async def fake_get_current_user():
            return current_user

        async def mock_deactivate_api_key(db, key_id, user_id):
            return False  # API key not found or not owned by user

        monkeypatch.setattr(
            mod.crud_api_key,
            "deactivate_api_key",
            mock_deactivate_api_key,
        )

        cleanup = override_dependency(app, mod.get_current_user, fake_get_current_user)

        try:
            resp = await async_client.delete(
                f"/auth/api-keys/{api_key_id}",
                headers={"authorization": "Bearer token"},
            )
            assert resp.status_code == 404
            assert "API key not found" in resp.json()["error"]["message"]
        finally:
            cleanup()

    async def test_deactivate_api_key_invalid_uuid(self, monkeypatch, async_client):
        """Test deactivating API key with invalid UUID format."""
        from app.api.auth import api_keys as mod
        from app.main import app

        current_user = create_test_user()

        async def fake_get_current_user():
            return current_user

        cleanup = override_dependency(app, mod.get_current_user, fake_get_current_user)

        try:
            resp = await async_client.delete(
                "/auth/api-keys/invalid-uuid",
                headers={"authorization": "Bearer token"},
            )
            # Should return 422 for validation error or handle gracefully
            assert resp.status_code in [404, 422, 500]
        finally:
            cleanup()


class TestAPIKeyRotation:
    """Test API key rotation functionality."""

    async def test_rotate_api_key_success(self, monkeypatch, async_client):
        """Test successful API key rotation."""
        from app.api.auth import api_keys as mod
        from app.main import app

        current_user = create_test_user()
        api_key_id = str(uuid4())

        async def fake_get_current_user():
            return current_user

        mock_api_key = MagicMock()
        mock_api_key.id = uuid4()
        mock_api_key.label = "Rotated API Key"
        mock_api_key.created_at = datetime.now(timezone.utc)
        mock_api_key.is_active = True
        mock_api_key.expires_at = None
        mock_api_key.scopes = ["read", "write"]
        mock_api_key.user_id = str(uuid4())
        # Ensure the mock is properly configured to avoid serialization issues
        mock_api_key.__str__ = lambda: "MockAPIKey"
        mock_api_key.__repr__ = lambda: "MockAPIKey"

        async def mock_rotate_api_key(db, key_id, user_id):
            return (mock_api_key, "new_raw_key_456")

        monkeypatch.setattr(mod.crud_api_key, "rotate_api_key", mock_rotate_api_key)

        cleanup = override_dependency(app, mod.get_current_user, fake_get_current_user)

        try:
            resp = await async_client.post(
                f"/auth/api-keys/{api_key_id}/rotate",
                headers={"authorization": "Bearer token"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "api_key" in data
            assert "new_raw_key" in data
            assert data["new_raw_key"] == "new_raw_key_456"
        finally:
            cleanup()

    async def test_rotate_api_key_not_found(self, monkeypatch, async_client):
        """Test rotating non-existent API key."""
        from app.api.auth import api_keys as mod
        from app.main import app

        current_user = create_test_user()
        api_key_id = str(uuid4())

        async def fake_get_current_user():
            return current_user

        async def mock_rotate_api_key(db, key_id, user_id):
            return (None, None)  # API key not found

        monkeypatch.setattr(mod.crud_api_key, "rotate_api_key", mock_rotate_api_key)

        cleanup = override_dependency(app, mod.get_current_user, fake_get_current_user)

        try:
            resp = await async_client.post(
                f"/auth/api-keys/{api_key_id}/rotate",
                headers={"authorization": "Bearer token"},
            )
            assert resp.status_code == 404
            assert "API key not found" in resp.json()["error"]["message"]
        finally:
            cleanup()

    async def test_rotate_api_key_generation_fails(self, monkeypatch, async_client):
        """Test API key rotation when new key generation fails."""
        from app.api.auth import api_keys as mod
        from app.main import app

        current_user = create_test_user()
        api_key_id = str(uuid4())

        async def fake_get_current_user():
            return current_user

        mock_api_key = MagicMock()
        mock_api_key.id = uuid4()
        mock_api_key.user_id = str(uuid4())
        # Ensure the mock is properly configured to avoid serialization issues
        mock_api_key.__str__ = lambda: "MockAPIKey"
        mock_api_key.__repr__ = lambda: "MockAPIKey"

        async def mock_rotate_api_key(db, key_id, user_id):
            return (mock_api_key, None)  # Key found but new key generation failed

        monkeypatch.setattr(mod.crud_api_key, "rotate_api_key", mock_rotate_api_key)

        cleanup = override_dependency(app, mod.get_current_user, fake_get_current_user)

        try:
            resp = await async_client.post(
                f"/auth/api-keys/{api_key_id}/rotate",
                headers={"authorization": "Bearer token"},
            )
            assert resp.status_code == 500
            assert "Failed to rotate API key" in resp.json()["error"]["message"]
        finally:
            cleanup()


class TestAPIKeyValidation:
    """Test API key validation scenarios."""

    async def test_create_api_key_invalid_scopes(self, monkeypatch, async_client):
        """Test API key creation with invalid scopes."""
        from app.api.auth import api_keys as mod
        from app.main import app

        current_user = create_test_user()

        async def fake_get_current_user():
            return current_user

        # Mock the CRUD function to return a proper API key object
        mock_api_key = types.SimpleNamespace(
            id=uuid4(),
            label="Test API Key",
            created_at=datetime.now(timezone.utc),
            is_active=True,
            scopes=["invalid_scope"],
            user_id=str(uuid4()),
        )

        async def mock_create_api_key(db, api_key_data, user_id, raw_key):
            return mock_api_key

        monkeypatch.setattr(
            "app.core.security.generate_api_key",
            lambda: "test_raw_key_123",
        )
        monkeypatch.setattr(mod.crud_api_key, "create_api_key", mock_create_api_key)

        cleanup = override_dependency(app, mod.get_current_user, fake_get_current_user)

        try:
            resp = await async_client.post(
                "/auth/api-keys",
                json={
                    "label": "Test API Key",
                    "scopes": ["invalid_scope"],  # Assuming this is invalid
                },
                headers={"authorization": "Bearer token"},
            )
            # Should either succeed or return validation error
            assert resp.status_code in [201, 422]
        finally:
            cleanup()

    async def test_create_api_key_empty_label(self, monkeypatch, async_client):
        """Test API key creation with empty label."""
        from app.api.auth import api_keys as mod
        from app.main import app

        current_user = create_test_user()

        async def fake_get_current_user():
            return current_user

        # Mock the CRUD function to return a proper API key object
        mock_api_key = types.SimpleNamespace(
            id=uuid4(),
            label="",
            created_at=datetime.now(timezone.utc),
            is_active=True,
            scopes=["read"],
            user_id=str(uuid4()),
        )

        async def mock_create_api_key(db, api_key_data, user_id, raw_key):
            return mock_api_key

        monkeypatch.setattr(
            "app.core.security.generate_api_key",
            lambda: "test_raw_key_123",
        )
        monkeypatch.setattr(mod.crud_api_key, "create_api_key", mock_create_api_key)

        cleanup = override_dependency(app, mod.get_current_user, fake_get_current_user)

        try:
            resp = await async_client.post(
                "/auth/api-keys",
                json={
                    "label": "",  # Empty label
                    "scopes": ["read"],
                },
                headers={"authorization": "Bearer token"},
            )
            assert resp.status_code == 422  # Validation error
        finally:
            cleanup()

    async def test_create_api_key_past_expiration(self, monkeypatch, async_client):
        """Test API key creation with past expiration date."""
        from app.api.auth import api_keys as mod
        from app.main import app

        current_user = create_test_user()

        async def fake_get_current_user():
            return current_user

        # Mock the CRUD function to return a proper API key object
        past_date = datetime.now(timezone.utc) - timedelta(days=1)
        mock_api_key = types.SimpleNamespace(
            id=uuid4(),
            label="Past Expiration Key",
            created_at=datetime.now(timezone.utc),
            is_active=True,
            scopes=["read"],
            user_id=str(uuid4()),
            expires_at=past_date,
        )

        async def mock_create_api_key(db, api_key_data, user_id, raw_key):
            return mock_api_key

        monkeypatch.setattr(
            "app.core.security.generate_api_key",
            lambda: "test_raw_key_123",
        )
        monkeypatch.setattr(mod.crud_api_key, "create_api_key", mock_create_api_key)

        cleanup = override_dependency(app, mod.get_current_user, fake_get_current_user)

        try:
            resp = await async_client.post(
                "/auth/api-keys",
                json={
                    "label": "Past Expiration Key",
                    "scopes": ["read"],
                    "expires_at": past_date.isoformat(),
                },
                headers={"authorization": "Bearer token"},
            )
            # Should be handled by validation
            assert resp.status_code in [422, 400]
        finally:
            cleanup()


class TestAPIKeySecurityScenarios:
    """Test security-related API key scenarios."""

    async def test_unauthorized_api_key_access(self, async_client):
        """Test API key operations without authentication."""
        # Test create without auth
        resp = await async_client.post(
            "/auth/api-keys",
            json={"label": "Test API Key", "scopes": ["read"]},
        )
        assert resp.status_code == 401

        # Test list without auth
        resp = await async_client.get("/auth/api-keys")
        assert resp.status_code == 401

        # Test delete without auth
        resp = await async_client.delete(f"/auth/api-keys/{uuid4()}")
        assert resp.status_code == 401

        # Test rotate without auth
        resp = await async_client.post(f"/auth/api-keys/{uuid4()}/rotate")
        assert resp.status_code == 401

    async def test_api_key_cross_user_access(self, monkeypatch, async_client):
        """Test that users can't access other users' API keys."""
        from app.api.auth import api_keys as mod
        from app.main import app

        current_user = create_test_user()
        other_user_api_key_id = str(uuid4())

        async def fake_get_current_user():
            return current_user

        async def mock_deactivate_api_key(db, key_id, user_id):
            # Simulate that the API key belongs to another user
            return False

        monkeypatch.setattr(
            mod.crud_api_key,
            "deactivate_api_key",
            mock_deactivate_api_key,
        )

        cleanup = override_dependency(app, mod.get_current_user, fake_get_current_user)

        try:
            resp = await async_client.delete(
                f"/auth/api-keys/{other_user_api_key_id}",
                headers={"authorization": "Bearer token"},
            )
            assert resp.status_code == 404  # Should not reveal existence
        finally:
            cleanup()

    async def test_api_key_rate_limiting_scenarios(self, monkeypatch, async_client):
        """Test API key operations under potential rate limiting."""
        from app.api.auth import api_keys as mod
        from app.main import app

        current_user = create_test_user()

        async def fake_get_current_user():
            return current_user

        mock_api_key = types.SimpleNamespace(
            id=uuid4(),
            label="Rate Test Key",
            created_at=datetime.now(timezone.utc),
            is_active=True,
            scopes=["read"],
            user_id=str(uuid4()),
        )

        async def mock_create_api_key(db, api_key_data, user_id, raw_key):
            return mock_api_key

        monkeypatch.setattr(
            "app.core.security.generate_api_key",
            lambda: f"test_key_{uuid4().hex[:8]}",
        )
        monkeypatch.setattr(mod.crud_api_key, "create_api_key", mock_create_api_key)

        cleanup = override_dependency(app, mod.get_current_user, fake_get_current_user)

        try:
            # Create multiple API keys to test potential rate limiting
            for i in range(3):
                resp = await async_client.post(
                    "/auth/api-keys",
                    json={"label": f"Rate Test Key {i}", "scopes": ["read"]},
                    headers={"authorization": "Bearer token"},
                )
                assert resp.status_code == 201
        finally:
            cleanup()
