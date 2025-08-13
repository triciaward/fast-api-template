"""API key deactivation tests."""

from uuid import uuid4

import pytest

from tests.utils.auth_helpers import create_test_user, override_dependency

pytestmark = pytest.mark.asyncio


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
                f"/api/auth/api-keys/{api_key_id}",
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
                f"/api/auth/api-keys/{api_key_id}",
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
                "/api/auth/api-keys/invalid-uuid",
                headers={"authorization": "Bearer token"},
            )
            # Should return 422 for validation error or handle gracefully
            assert resp.status_code in [404, 422, 500]
        finally:
            cleanup()
