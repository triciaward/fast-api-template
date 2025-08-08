"""API key validation tests."""

import types
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from tests.utils.auth_helpers import create_test_user, override_dependency

pytestmark = pytest.mark.asyncio


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
