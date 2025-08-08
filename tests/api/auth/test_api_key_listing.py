"""API key listing tests."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from tests.utils.auth_helpers import create_test_user, override_dependency

pytestmark = pytest.mark.asyncio


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
