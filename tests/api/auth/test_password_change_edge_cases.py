"""Password change edge case tests."""

import types

import pytest

from tests.utils.auth_helpers import create_test_user, override_dependency

pytestmark = pytest.mark.asyncio


class TestPasswordChangeEdgeCases:
    """Test edge cases for password change functionality."""

    async def test_change_password_user_not_in_database(
        self,
        monkeypatch,
        async_client,
    ):
        """Test password change when user is not found in database."""
        from app.api.auth import password_management as mod
        from app.main import app

        current_user = create_test_user()

        async def fake_get_current_user():
            return current_user

        # Mock that user is not found in database
        async def mock_get_user_by_email(db, email):
            return None

        monkeypatch.setattr(mod.crud_user, "get_user_by_email", mock_get_user_by_email)

        cleanup = override_dependency(app, mod.get_current_user, fake_get_current_user)

        try:
            resp = await async_client.post(
                "/api/auth/change-password",
                json={"current_password": "OldPass123!", "new_password": "NewPass123!"},
                headers={"authorization": "Bearer token", "user-agent": "pytest"},
            )
            assert resp.status_code == 500
            assert "User not found" in resp.json()["error"]["message"]
        finally:
            cleanup()

    async def test_change_password_update_fails(self, monkeypatch, async_client):
        """Test password change when database update fails."""
        from app.api.auth import password_management as mod
        from app.main import app

        current_user = create_test_user()

        async def fake_get_current_user():
            return current_user

        async def fake_get_user_by_email(db, email):
            return types.SimpleNamespace(
                hashed_password="hashed_old_password",
                id=current_user.id,
            )

        # Mock successful password verification but failed update
        async def mock_update_password(db, user_id, password):
            return False

        monkeypatch.setattr(mod.crud_user, "get_user_by_email", fake_get_user_by_email)
        monkeypatch.setattr(mod, "verify_password", lambda p, h: True)
        monkeypatch.setattr(mod.crud_user, "update_user_password", mock_update_password)

        cleanup = override_dependency(app, mod.get_current_user, fake_get_current_user)

        try:
            resp = await async_client.post(
                "/api/auth/change-password",
                json={"current_password": "OldPass123!", "new_password": "NewPass123!"},
                headers={"authorization": "Bearer token", "user-agent": "pytest"},
            )
            assert resp.status_code == 500
            assert "Failed to change password" in resp.json()["error"]["message"]
        finally:
            cleanup()

    async def test_change_password_audit_log_success(self, monkeypatch, async_client):
        """Test password change with successful audit logging."""
        from app.api.auth import password_management as mod
        from app.main import app

        current_user = create_test_user()
        audit_log_called = False

        async def fake_get_current_user():
            return current_user

        async def fake_get_user_by_email(db, email):
            return types.SimpleNamespace(
                hashed_password="hashed_old_password",
                id=current_user.id,
            )

        async def fake_log_password_change(db, request, user, change_type):
            nonlocal audit_log_called
            audit_log_called = True
            assert change_type == "password_change"

        async def mock_update_password(db, user_id, password):
            return True

        monkeypatch.setattr(mod.crud_user, "get_user_by_email", fake_get_user_by_email)
        monkeypatch.setattr(mod, "verify_password", lambda p, h: True)
        monkeypatch.setattr(mod.crud_user, "update_user_password", mock_update_password)
        monkeypatch.setattr(mod, "log_password_change", fake_log_password_change)

        cleanup = override_dependency(app, mod.get_current_user, fake_get_current_user)

        try:
            resp = await async_client.post(
                "/api/auth/change-password",
                json={"current_password": "OldPass123!", "new_password": "NewPass123!"},
                headers={"authorization": "Bearer token", "user-agent": "pytest"},
            )
            assert resp.status_code == 200
            assert "successfully" in resp.json()["detail"].lower()
            assert audit_log_called
        finally:
            cleanup()

    async def test_change_password_unexpected_error(self, monkeypatch, async_client):
        """Test password change with unexpected error."""
        from app.api.auth import password_management as mod
        from app.main import app

        current_user = create_test_user()

        async def fake_get_current_user():
            return current_user

        async def error_function(*args, **kwargs):
            raise Exception("Database connection lost")

        monkeypatch.setattr(mod.crud_user, "get_user_by_email", error_function)

        cleanup = override_dependency(app, mod.get_current_user, fake_get_current_user)

        try:
            resp = await async_client.post(
                "/api/auth/change-password",
                json={"current_password": "OldPass123!", "new_password": "NewPass123!"},
                headers={"authorization": "Bearer token", "user-agent": "pytest"},
            )
            assert resp.status_code == 500
            assert "Password change failed" in resp.json()["error"]["message"]
        finally:
            cleanup()
