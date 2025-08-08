"""Comprehensive tests for bootstrap superuser script."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.bootstrap_superuser import bootstrap_superuser, create_superuser
from app.models.auth.user import User
from app.schemas.auth.user import UserCreate

pytestmark = pytest.mark.unit


class TestCreateSuperuser:
    """Test create_superuser function."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def mock_settings(self, monkeypatch):
        """Mock settings for testing."""
        monkeypatch.setattr(
            "app.bootstrap_superuser.settings.FIRST_SUPERUSER",
            "admin@example.com",
        )
        monkeypatch.setattr(
            "app.bootstrap_superuser.settings.FIRST_SUPERUSER_PASSWORD",
            "SecurePass123!",
        )

    @pytest.mark.asyncio
    async def test_create_superuser_success(self, mock_db, mock_settings):
        """Test successful superuser creation."""
        # Mock that no existing user is found
        with patch("app.bootstrap_superuser.get_user_by_email") as mock_get_user:
            mock_get_user.return_value = None

            # Mock successful user creation
            with patch("app.crud.auth.user.create_user") as mock_create_user:
                mock_user = User()
                mock_user.id = uuid4()
                mock_user.email = "admin@example.com"
                mock_user.username = "admin_example"
                mock_create_user.return_value = mock_user

                # Mock validation functions
                with patch(
                    "app.core.security.validate_username",
                ) as mock_validate_username:
                    mock_validate_username.return_value = (True, None)

                    with patch(
                        "app.core.security.validate_password",
                    ) as mock_validate_password:
                        mock_validate_password.return_value = (True, None)

                        result = await create_superuser(
                            db=mock_db,
                            email="admin@example.com",
                            password="SecurePass123!",
                        )

                        assert result is True
                        mock_get_user.assert_called_once_with(
                            mock_db,
                            "admin@example.com",
                        )
                        mock_create_user.assert_called_once()

                        # Verify UserCreate data
                        call_args = mock_create_user.call_args[0]
                        user_data = call_args[1]
                        assert isinstance(user_data, UserCreate)
                        assert user_data.email == "admin@example.com"
                        assert user_data.is_superuser is True

    @pytest.mark.asyncio
    async def test_create_superuser_already_exists(self, mock_db, mock_settings):
        """Test superuser creation when user already exists."""
        # Mock that existing user is found
        with patch("app.bootstrap_superuser.get_user_by_email") as mock_get_user:
            existing_user = User()
            existing_user.email = "admin@example.com"
            mock_get_user.return_value = existing_user

            result = await create_superuser(
                db=mock_db,
                email="admin@example.com",
                password="SecurePass123!",
            )

            assert result is False
            mock_get_user.assert_called_once_with(mock_db, "admin@example.com")

    @pytest.mark.asyncio
    async def test_create_superuser_username_generation(self, mock_db, mock_settings):
        """Test username generation logic."""
        with patch("app.bootstrap_superuser.get_user_by_email") as mock_get_user:
            mock_get_user.return_value = None

            with patch("app.crud.auth.user.create_user") as mock_create_user:
                mock_user = User()
                mock_user.id = uuid4()
                mock_user.email = "admin@example.com"
                mock_user.username = "admin_example"
                mock_create_user.return_value = mock_user

                with patch(
                    "app.core.security.validate_username",
                ) as mock_validate_username:
                    mock_validate_username.return_value = (True, None)

                    with patch(
                        "app.core.security.validate_password",
                    ) as mock_validate_password:
                        mock_validate_password.return_value = (True, None)

                        await create_superuser(
                            db=mock_db,
                            email="admin@example.com",
                            password="SecurePass123!",
                        )

                        # Check that username was generated from email
                        user_data = mock_create_user.call_args[0][1]
                        assert user_data.username == "admin_example"

    @pytest.mark.asyncio
    async def test_create_superuser_custom_username(self, mock_db, mock_settings):
        """Test superuser creation with custom username."""
        with patch("app.bootstrap_superuser.get_user_by_email") as mock_get_user:
            mock_get_user.return_value = None

            with patch("app.crud.auth.user.create_user") as mock_create_user:
                mock_user = User()
                mock_user.id = uuid4()
                mock_user.email = "admin@example.com"
                mock_user.username = "custom_admin"
                mock_create_user.return_value = mock_user

                with patch(
                    "app.core.security.validate_username",
                ) as mock_validate_username:
                    mock_validate_username.return_value = (True, None)

                    with patch(
                        "app.core.security.validate_password",
                    ) as mock_validate_password:
                        mock_validate_password.return_value = (True, None)

                        await create_superuser(
                            db=mock_db,
                            email="admin@example.com",
                            password="SecurePass123!",
                            username="custom_admin",
                        )

                        user_data = mock_create_user.call_args[0][1]
                        assert user_data.username == "custom_admin"

    @pytest.mark.asyncio
    async def test_create_superuser_invalid_username_fallback(
        self,
        mock_db,
        mock_settings,
    ):
        """Test fallback when generated username is invalid."""
        with patch("app.bootstrap_superuser.get_user_by_email") as mock_get_user:
            mock_get_user.return_value = None

            with patch("app.crud.auth.user.create_user") as mock_create_user:
                mock_user = User()
                mock_user.id = uuid4()
                mock_user.email = "a@example.com"  # Short email
                mock_user.username = "admin_example"
                mock_create_user.return_value = mock_user

                with patch(
                    "app.core.security.validate_username",
                ) as mock_validate_username:
                    # First call (generated username) fails, second call (fallback) succeeds
                    mock_validate_username.side_effect = [
                        (False, "Too short"),
                        (True, None),
                    ]

                    with patch(
                        "app.core.security.validate_password",
                    ) as mock_validate_password:
                        mock_validate_password.return_value = (True, None)

                        result = await create_superuser(
                            db=mock_db,
                            email="a@example.com",
                            password="SecurePass123!",
                        )

                        assert result is True
                        assert mock_validate_username.call_count == 2

    @pytest.mark.asyncio
    async def test_create_superuser_username_validation_fails(
        self,
        mock_db,
        mock_settings,
    ):
        """Test when username validation fails completely."""
        with patch("app.bootstrap_superuser.get_user_by_email") as mock_get_user:
            mock_get_user.return_value = None

            with patch("app.core.security.validate_username") as mock_validate_username:
                # Both generated and fallback usernames fail validation
                mock_validate_username.return_value = (False, "Invalid username")

                result = await create_superuser(
                    db=mock_db,
                    email="admin@example.com",
                    password="SecurePass123!",
                )

                assert result is False

    @pytest.mark.asyncio
    async def test_create_superuser_password_validation_fallback(
        self,
        mock_db,
        mock_settings,
    ):
        """Test password validation with fallback to default password."""
        with patch("app.bootstrap_superuser.get_user_by_email") as mock_get_user:
            mock_get_user.return_value = None

            with patch("app.crud.auth.user.create_user") as mock_create_user:
                mock_user = User()
                mock_user.id = uuid4()
                mock_user.email = "admin@example.com"
                mock_user.username = "admin_example"
                mock_create_user.return_value = mock_user

                with patch(
                    "app.core.security.validate_username",
                ) as mock_validate_username:
                    mock_validate_username.return_value = (True, None)

                    with patch(
                        "app.core.security.validate_password",
                    ) as mock_validate_password:
                        mock_validate_password.return_value = (False, "Weak password")

                        result = await create_superuser(
                            db=mock_db,
                            email="admin@example.com",
                            password="weak",
                        )

                        assert result is True
                        # Verify default password was used
                        user_data = mock_create_user.call_args[0][1]
                        assert user_data.password == "Admin123!"

    @pytest.mark.asyncio
    async def test_create_superuser_creation_exception(self, mock_db, mock_settings):
        """Test handling of exceptions during user creation."""
        with patch("app.bootstrap_superuser.get_user_by_email") as mock_get_user:
            mock_get_user.return_value = None

            with patch("app.crud.auth.user.create_user") as mock_create_user:
                mock_create_user.side_effect = Exception("Database error")

                with patch(
                    "app.core.security.validate_username",
                ) as mock_validate_username:
                    mock_validate_username.return_value = (True, None)

                    with patch(
                        "app.core.security.validate_password",
                    ) as mock_validate_password:
                        mock_validate_password.return_value = (True, None)

                        result = await create_superuser(
                            db=mock_db,
                            email="admin@example.com",
                            password="SecurePass123!",
                        )

                        assert result is False


class TestBootstrapSuperuser:
    """Test bootstrap_superuser function."""

    @pytest.fixture
    def mock_settings_configured(self, monkeypatch):
        """Mock configured settings."""
        monkeypatch.setattr(
            "app.bootstrap_superuser.settings.FIRST_SUPERUSER",
            "admin@example.com",
        )
        monkeypatch.setattr(
            "app.bootstrap_superuser.settings.FIRST_SUPERUSER_PASSWORD",
            "SecurePass123!",
        )

    @pytest.fixture
    def mock_settings_not_configured(self, monkeypatch):
        """Mock unconfigured settings."""
        monkeypatch.setattr("app.bootstrap_superuser.settings.FIRST_SUPERUSER", None)
        monkeypatch.setattr(
            "app.bootstrap_superuser.settings.FIRST_SUPERUSER_PASSWORD",
            None,
        )

    @pytest.mark.asyncio
    async def test_bootstrap_superuser_not_configured(
        self,
        mock_settings_not_configured,
    ):
        """Test bootstrap when environment variables are not set."""
        await bootstrap_superuser()
        # Should complete without errors, just skip creation

    @pytest.mark.asyncio
    async def test_bootstrap_superuser_existing_superuser(
        self,
        mock_settings_configured,
    ):
        """Test bootstrap when superuser already exists."""
        mock_db = AsyncMock()

        # Mock existing superuser
        existing_superuser = User()
        existing_superuser.email = "existing@example.com"
        existing_superuser.is_superuser = True

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [existing_superuser]

        with patch("app.bootstrap_superuser.get_db") as mock_get_db:
            mock_get_db.return_value.__aiter__.return_value = [mock_db]

            with patch.object(mock_db, "execute") as mock_execute:
                mock_execute.return_value = mock_result

                await bootstrap_superuser()

                # Should check for existing superusers but not create new one
                mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_bootstrap_superuser_success(self, mock_settings_configured):
        """Test successful superuser bootstrap."""
        mock_db = AsyncMock()

        # Mock no existing superusers
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        with patch("app.bootstrap_superuser.get_db") as mock_get_db:
            mock_get_db.return_value.__aiter__.return_value = [mock_db]

            with patch.object(mock_db, "execute") as mock_execute:
                mock_execute.return_value = mock_result

                with patch(
                    "app.bootstrap_superuser.create_superuser",
                ) as mock_create_superuser:
                    mock_create_superuser.return_value = True

                    await bootstrap_superuser()

                    mock_create_superuser.assert_called_once_with(
                        db=mock_db,
                        email="admin@example.com",
                        password="SecurePass123!",
                    )

    @pytest.mark.asyncio
    async def test_bootstrap_superuser_creation_fails(self, mock_settings_configured):
        """Test bootstrap when superuser creation fails."""
        mock_db = AsyncMock()

        # Mock no existing superusers
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        with patch("app.bootstrap_superuser.get_db") as mock_get_db:
            mock_get_db.return_value.__aiter__.return_value = [mock_db]

            with patch.object(mock_db, "execute") as mock_execute:
                mock_execute.return_value = mock_result

                with patch(
                    "app.bootstrap_superuser.create_superuser",
                ) as mock_create_superuser:
                    mock_create_superuser.return_value = False

                    await bootstrap_superuser()

                    # Should attempt creation but handle failure gracefully
                    mock_create_superuser.assert_called_once()

    @pytest.mark.asyncio
    async def test_bootstrap_superuser_database_exception(
        self,
        mock_settings_configured,
    ):
        """Test bootstrap with database exception."""
        mock_db = AsyncMock()

        with patch("app.bootstrap_superuser.get_db") as mock_get_db:
            mock_get_db.return_value.__aiter__.return_value = [mock_db]

            with patch.object(mock_db, "execute") as mock_execute:
                mock_execute.side_effect = Exception("Database connection error")

                # Should handle exception gracefully
                await bootstrap_superuser()


class TestMainFunction:
    """Test main function for running bootstrap script."""

    def test_main_function(self):
        """Test main function execution."""
        with patch("app.bootstrap_superuser.asyncio.run") as mock_asyncio_run:
            from app.bootstrap_superuser import main

            main()

            mock_asyncio_run.assert_called_once()
            # Verify the correct coroutine was passed
            call_args = mock_asyncio_run.call_args[0][0]
            assert asyncio.iscoroutine(call_args)
            # Close the coroutine to avoid RuntimeWarning about un-awaited coroutine
            call_args.close()
