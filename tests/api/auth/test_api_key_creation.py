"""API key creation tests."""

import types
from datetime import datetime, timedelta, timezone
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
