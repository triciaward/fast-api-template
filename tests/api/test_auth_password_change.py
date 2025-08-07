import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.crud import user as crud_user
from tests.template_tests.conftest import TestingSyncSessionLocal


@pytest.mark.skip(
    reason="Requires complex password change functionality - not implemented yet",
)
class TestPasswordChange:
    """Test password change endpoint."""

    def test_change_password_success(self, client: TestClient) -> None:
        """Test successful password change."""
        # Create a test user through the API
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "OldPassword123!",
            "is_superuser": False,
        }

        # Register the user
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201

        # Verify the user manually (simulate email verification)
        with TestingSyncSessionLocal() as db:
            user = crud_user.get_user_by_email_sync(db, str(user_data["email"]))
            assert user is not None
            crud_user.verify_user_sync(db, str(user.id))

        # Login to get access token
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "test@example.com",
                "password": "OldPassword123!",
            },
        )
        assert login_response.status_code == 200
        token_data = login_response.json()
        access_token = token_data["access_token"]

        # Change password
        response = client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "current_password": "OldPassword123!",
                "new_password": "NewPassword456!",
            },
        )

        assert response.status_code == 200
        assert response.json() == {"detail": "Password updated successfully"}

        # Verify the password was actually changed by trying to login with new password
        new_login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "test@example.com",
                "password": "NewPassword456!",
            },
        )
        assert new_login_response.status_code == 200

        # Verify old password no longer works
        old_login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "test@example.com",
                "password": "OldPassword123!",
            },
        )
        assert old_login_response.status_code == 401

    def test_change_password_wrong_current_password(self, client: TestClient) -> None:
        """Test password change with incorrect current password."""
        # Create a test user through the API
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "CorrectPassword123!",
            "is_superuser": False,
        }

        # Register the user
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201

        # Verify the user manually (simulate email verification)
        with TestingSyncSessionLocal() as db:
            user = crud_user.get_user_by_email_sync(db, str(user_data["email"]))
            assert user is not None
            crud_user.verify_user_sync(db, str(user.id))

        # Login to get access token
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "test@example.com",
                "password": "CorrectPassword123!",
            },
        )
        assert login_response.status_code == 200
        token_data = login_response.json()
        access_token = token_data["access_token"]

        # Try to change password with wrong current password
        response = client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "current_password": "WrongPassword123!",
                "new_password": "NewPassword456!",
            },
        )

        assert response.status_code == 400
        assert response.json() == {"detail": "Incorrect current password"}

        # Verify the password was not changed by trying to login with old password
        old_login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "test@example.com",
                "password": "CorrectPassword123!",
            },
        )
        assert old_login_response.status_code == 200

    def test_change_password_weak_new_password(self, client: TestClient) -> None:
        """Test password change with weak new password."""
        # Create a test user through the API
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "CorrectPassword123!",
            "is_superuser": False,
        }

        # Register the user
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201

        # Verify the user manually (simulate email verification)
        with TestingSyncSessionLocal() as db:
            user = crud_user.get_user_by_email_sync(db, str(user_data["email"]))
            assert user is not None
            crud_user.verify_user_sync(db, str(user.id))

        # Login to get access token
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "test@example.com",
                "password": "CorrectPassword123!",
            },
        )
        assert login_response.status_code == 200
        token_data = login_response.json()
        access_token = token_data["access_token"]

        # Try to change password with weak new password
        response = client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "current_password": "CorrectPassword123!",
                "new_password": "weak",
            },
        )

        assert response.status_code == 422  # Validation error
        error_detail = response.json()["detail"]
        assert any(
            "Password must be at least 8 characters long" in str(error)
            for error in error_detail
        )

    def test_change_password_oauth_user(self, client: TestClient) -> None:
        """Test password change attempt by OAuth user."""
        # Create an OAuth user directly in the database
        with TestingSyncSessionLocal() as db:
            oauth_user = crud_user.create_oauth_user_sync(
                db,
                email="oauth@example.com",
                username="oauthuser",
                oauth_provider="google",
                oauth_id="google123",
                oauth_email="oauth@example.com",
            )

        # Create access token for the OAuth user
        access_token = create_access_token(subject=oauth_user.email)

        # Try to change password (this should fail for OAuth users)
        response = client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "current_password": "SomePassword123!",
                "new_password": "NewPassword456!",
            },
        )

        assert response.status_code == 400
        assert response.json() == {"detail": "OAuth users cannot change password"}

    def test_change_password_oauth_user_regular_user(self, client: TestClient) -> None:
        """Test password change for regular user (should work)."""
        # Create a regular user first
        user_data = {
            "email": "regular@example.com",
            "username": "regularuser",
            "password": "SomePassword123!",
            "is_superuser": False,
        }

        # Register the user
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201

        # Verify the user manually (simulate email verification)
        with TestingSyncSessionLocal() as db:
            user = crud_user.get_user_by_email_sync(db, str(user_data["email"]))
            assert user is not None
            crud_user.verify_user_sync(db, str(user.id))

        # Login to get access token
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "regular@example.com",
                "password": "SomePassword123!",
            },
        )
        assert login_response.status_code == 200
        token_data = login_response.json()
        access_token = token_data["access_token"]

        # Try to change password (this should work for regular users)
        response = client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "current_password": "SomePassword123!",
                "new_password": "NewPassword456!",
            },
        )

        # This should succeed for regular users
        assert response.status_code == 200

    def test_change_password_no_auth_token(self, client: TestClient) -> None:
        """Test password change without authentication token."""
        response = client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "OldPassword123!",
                "new_password": "NewPassword456!",
            },
        )

        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    def test_change_password_invalid_token(self, client: TestClient) -> None:
        """Test password change with invalid token."""
        response = client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": "Bearer invalid_token"},
            json={
                "current_password": "OldPassword123!",
                "new_password": "NewPassword456!",
            },
        )

        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]

    def test_change_password_invalidates_reset_tokens(self, client: TestClient) -> None:
        """Test that password change invalidates any existing reset tokens."""
        # Create a test user through the API
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "OldPassword123!",
            "is_superuser": False,
        }

        # Register the user
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201

        # Verify the user manually (simulate email verification)
        with TestingSyncSessionLocal() as db:
            user = crud_user.get_user_by_email_sync(db, str(user_data["email"]))
            assert user is not None
            crud_user.verify_user_sync(db, str(user.id))

        # Login to get access token
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "test@example.com",
                "password": "OldPassword123!",
            },
        )
        assert login_response.status_code == 200
        token_data = login_response.json()
        access_token = token_data["access_token"]

        # Change password
        response = client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "current_password": "OldPassword123!",
                "new_password": "NewPassword456!",
            },
        )

        assert response.status_code == 200

        # Note: Testing token invalidation would require direct database access
        # or a separate endpoint to check token status. For now, we verify
        # the password change worked by testing login with new password
        new_login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "test@example.com",
                "password": "NewPassword456!",
            },
        )
        assert new_login_response.status_code == 200
