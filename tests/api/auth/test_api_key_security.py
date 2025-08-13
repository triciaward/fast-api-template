"""API key security tests."""

import types
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from tests.utils.auth_helpers import create_test_user, override_dependency

pytestmark = pytest.mark.asyncio


class TestAPIKeySecurityScenarios:
    """Test security-related API key scenarios."""

    async def test_unauthorized_api_key_access(self, async_client):
        """Test API key operations without authentication."""
        # Test create without auth
        resp = await async_client.post(
            "/api/auth/api-keys",
            json={"label": "Test API Key", "scopes": ["read"]},
        )
        assert resp.status_code == 401

        # Test list without auth
        resp = await async_client.get("/api/auth/api-keys")
        assert resp.status_code == 401

        # Test delete without auth
        resp = await async_client.delete(f"/api/auth/api-keys/{uuid4()}")
        assert resp.status_code == 401

        # Test rotate without auth
        resp = await async_client.post(f"/api/auth/api-keys/{uuid4()}/rotate")
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
                f"/api/auth/api-keys/{other_user_api_key_id}",
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
                    "/api/auth/api-keys",
                    json={"label": f"Rate Test Key {i}", "scopes": ["read"]},
                    headers={"authorization": "Bearer token"},
                )
                assert resp.status_code == 201
        finally:
            cleanup()
