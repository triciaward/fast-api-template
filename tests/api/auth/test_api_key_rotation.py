"""API key rotation tests."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from tests.utils.auth_helpers import create_test_user, override_dependency

pytestmark = pytest.mark.asyncio


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
                f"/api/auth/api-keys/{api_key_id}/rotate",
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
                f"/api/auth/api-keys/{api_key_id}/rotate",
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
                f"/api/auth/api-keys/{api_key_id}/rotate",
                headers={"authorization": "Bearer token"},
            )
            assert resp.status_code == 500
            assert "Failed to rotate API key" in resp.json()["error"]["message"]
        finally:
            cleanup()
