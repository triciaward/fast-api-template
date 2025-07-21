from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

pytestmark = pytest.mark.usefixtures("patch_email_service_is_configured")


@pytest.fixture(autouse=True)
def patch_email_service_is_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services.email import email_service

    monkeypatch.setattr(email_service, "is_configured", lambda: True)


@pytest.mark.skip(reason="Requires complex OAuth functionality - not implemented yet")
class TestOAuthAuthEndpoints:
    def test_oauth_login_unsupported_provider(self, client: TestClient) -> None:
        """Test OAuth login with unsupported provider."""
        response = client.post(
            "/api/v1/auth/oauth/login",
            json={"provider": "unsupported", "access_token": "test_token"},
        )
        assert response.status_code == 422
        assert "Provider must be 'google' or 'apple'" in str(response.json())

    def test_oauth_login_google_not_configured(self, client: TestClient) -> None:
        """Test OAuth login when Google is not configured."""
        with patch(
            "app.services.oauth.oauth_service.is_provider_configured",
            return_value=False,
        ):
            response = client.post(
                "/api/v1/auth/oauth/login",
                json={"provider": "google", "access_token": "test_token"},
            )
            assert response.status_code == 400
            assert "Google OAuth not configured" in response.json()["detail"]

    def test_oauth_login_apple_not_configured(self, client: TestClient) -> None:
        """Test OAuth login when Apple is not configured."""
        with patch(
            "app.services.oauth.oauth_service.is_provider_configured",
            return_value=False,
        ):
            response = client.post(
                "/api/v1/auth/oauth/login",
                json={"provider": "apple", "access_token": "test_token"},
            )
            assert response.status_code == 400
            assert "Apple OAuth not configured" in response.json()["detail"]

    def test_oauth_login_google_success_new_user(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test successful OAuth login for new Google user."""
        with patch("app.services.oauth.settings") as mock_settings, patch(
            "app.services.oauth.oauth_service.verify_google_token"
        ) as mock_verify:
            mock_settings.GOOGLE_CLIENT_ID = "test_client_id"
            mock_verify.return_value = {
                "sub": "google_user_id",
                "email": "newuser@example.com",
                "name": "New User",
            }

            response = client.post(
                "/api/v1/auth/oauth/login",
                json={"provider": "google", "access_token": "test_token"},
            )
            assert response.status_code == 200
            token_data = response.json()
            assert "access_token" in token_data
            assert token_data["token_type"] == "bearer"

    def test_oauth_login_google_existing_user(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test successful OAuth login for existing Google user."""
        # Create existing OAuth user
        from app.models.models import User

        user = User(
            email="existing@example.com",
            username="existinguser",
            hashed_password=None,
            oauth_provider="google",
            oauth_id="google_user_id",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        with patch("app.services.oauth.settings") as mock_settings, patch(
            "app.services.oauth.oauth_service.verify_google_token"
        ) as mock_verify:
            mock_settings.GOOGLE_CLIENT_ID = "test_client_id"
            mock_verify.return_value = {
                "sub": "google_user_id",
                "email": "existing@example.com",
                "name": "Existing User",
            }

            response = client.post(
                "/api/v1/auth/oauth/login",
                json={"provider": "google", "access_token": "test_token"},
            )
            assert response.status_code == 200
            token_data = response.json()
            assert "access_token" in token_data
            assert token_data["token_type"] == "bearer"

    def test_oauth_login_email_already_registered(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test OAuth login when email is already registered with different provider."""
        # Create user with different OAuth provider
        from app.models.models import User

        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            oauth_provider="apple",
            oauth_id="apple_user_id",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        with patch("app.services.oauth.settings") as mock_settings, patch(
            "app.services.oauth.oauth_service.verify_google_token"
        ) as mock_verify:
            mock_settings.GOOGLE_CLIENT_ID = "test_client_id"
            mock_verify.return_value = {
                "sub": "google_user_id",
                "email": "test@example.com",
                "name": "Test User",
            }

            response = client.post(
                "/api/v1/auth/oauth/login",
                json={"provider": "google", "access_token": "test_token"},
            )
            assert response.status_code == 400
            assert (
                "Email already registered with different method"
                in response.json()["detail"]
            )

    def test_oauth_login_invalid_token(self, client: TestClient) -> None:
        """Test OAuth login with invalid token."""
        with patch("app.services.oauth.settings") as mock_settings, patch(
            "app.services.oauth.oauth_service.verify_google_token"
        ) as mock_verify:
            mock_settings.GOOGLE_CLIENT_ID = "test_client_id"
            mock_verify.return_value = None

            response = client.post(
                "/api/v1/auth/oauth/login",
                json={"provider": "google", "access_token": "invalid_token"},
            )
            assert response.status_code == 400
            assert "Invalid Google token" in response.json()["detail"]

    def test_oauth_login_missing_user_info(self, client: TestClient) -> None:
        """Test OAuth login with missing user info."""
        with patch("app.services.oauth.settings") as mock_settings, patch(
            "app.services.oauth.oauth_service.verify_google_token"
        ) as mock_verify:
            mock_settings.GOOGLE_CLIENT_ID = "test_client_id"
            # Missing email and name
            mock_verify.return_value = {"sub": "google_user_id"}

            response = client.post(
                "/api/v1/auth/oauth/login",
                json={"provider": "google", "access_token": "test_token"},
            )
            assert response.status_code == 400
            assert "Invalid OAuth user info" in response.json()["detail"]

    def test_get_oauth_providers_none_configured(self, client: TestClient) -> None:
        """Test getting OAuth providers when none are configured."""
        with patch(
            "app.services.oauth.oauth_service.is_provider_configured",
            return_value=False,
        ):
            response = client.get("/api/v1/auth/oauth/providers")
            assert response.status_code == 200
            data = response.json()
            assert data["providers"] == []

    def test_get_oauth_providers_google_configured(self, client: TestClient) -> None:
        """Test getting OAuth providers when Google is configured."""
        with patch(
            "app.services.oauth.oauth_service.is_provider_configured"
        ) as mock_configured, patch(
            "app.services.oauth.oauth_service.get_oauth_provider_config"
        ) as mock_config:
            mock_configured.side_effect = lambda provider: provider == "google"
            mock_config.return_value = {"client_id": "test_client_id"}

            response = client.get("/api/v1/auth/oauth/providers")
            assert response.status_code == 200
            data = response.json()
            assert "google" in data["providers"]
            assert "apple" not in data["providers"]

    def test_get_oauth_providers_both_configured(self, client: TestClient) -> None:
        """Test getting OAuth providers when both are configured."""
        with patch(
            "app.services.oauth.oauth_service.is_provider_configured", return_value=True
        ), patch(
            "app.services.oauth.oauth_service.get_oauth_provider_config"
        ) as mock_config:
            mock_config.return_value = {"client_id": "test_client_id"}

            response = client.get("/api/v1/auth/oauth/providers")
            assert response.status_code == 200
            data = response.json()
            assert "google" in data["providers"]
            assert "apple" in data["providers"]


@pytest.mark.skip(reason="Requires complex OAuth functionality - not implemented yet")
class TestOAuthCRUDOperations:
    def test_get_user_by_oauth_id_sync(self, sync_db_session: Session) -> None:
        """Test getting user by OAuth ID using sync CRUD."""
        from app.crud import user as crud_user
        from app.models.models import User

        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=None,
            oauth_provider="google",
            oauth_id="google_user_id",
            is_verified=True,
        )
        sync_db_session.add(user)
        sync_db_session.commit()

        found_user = crud_user.get_user_by_oauth_id_sync(
            sync_db_session, "google", "google_user_id"
        )
        assert found_user is not None
        assert found_user.email == "test@example.com"

    def test_create_oauth_user_sync(self, sync_db_session: Session) -> None:
        """Test creating OAuth user using sync CRUD."""
        from app.crud import user as crud_user

        user = crud_user.create_oauth_user_sync(
            db=sync_db_session,
            email="oauth@example.com",
            username="oauthuser",
            oauth_provider="google",
            oauth_id="google_user_id",
            oauth_email="oauth@example.com",
        )

        assert user.email == "oauth@example.com"
        assert user.username == "oauthuser"
        assert user.oauth_provider == "google"
        assert user.oauth_id == "google_user_id"
        assert user.is_verified is True
        assert user.hashed_password is None  # type: ignore[unreachable]
