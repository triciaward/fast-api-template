"""
Unit tests for setup scripts.

Tests the comprehensive setup, verification, and fix scripts to ensure
they work correctly and handle various scenarios.

These tests are template-specific and should be excluded when running
tests for user applications.
"""

import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.mark.template_only
class TestSetupComprehensiveScript:
    """Test the comprehensive setup script functionality."""

    @patch("subprocess.run")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    def test_setup_script_creates_env_file(self, mock_exists, mock_file, mock_run):
        """Test that the setup script creates a .env file when it doesn't exist."""
        # Mock file existence checks
        mock_exists.side_effect = lambda path: {
            ".env": False,
            "venv": False,
            "alembic.ini": True,
            "app/bootstrap_superuser.py": True,
        }.get(path, True)

        # Mock subprocess calls
        mock_run.return_value.returncode = 0

        # Test the script logic (simplified version)
        from scripts.setup_comprehensive import create_env_file

        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            create_env_file(env_path)

            # Verify .env file was created
            assert env_path.exists()

            # Check that it contains required variables
            content = env_path.read_text()
            assert "POSTGRES_DB=fastapi_template" in content
            assert "POSTGRES_USER=postgres" in content
            assert "DATABASE_URL=" in content
            assert "BACKEND_CORS_ORIGINS=" in content

    @patch("subprocess.run")
    def test_setup_script_handles_missing_docker(self, mock_run):
        """Test that the script handles missing Docker gracefully."""
        # Mock docker command not found
        mock_run.side_effect = FileNotFoundError("docker: command not found")

        # Test the script logic (simplified version)
        from scripts.setup_comprehensive import check_docker_services

        result = check_docker_services()
        assert result is False

    @patch("subprocess.run")
    def test_setup_script_handles_migration_conflicts(self, mock_run):
        """Test that the script handles migration conflicts correctly."""
        # Mock alembic upgrade failing, then stamp succeeding
        mock_run.side_effect = [
            # alembic upgrade head fails
            subprocess.CalledProcessError(1, "alembic"),
            MagicMock(returncode=0),  # alembic stamp head succeeds
        ]

        # Test the script logic (simplified version)
        from scripts.setup_comprehensive import run_migrations

        result = run_migrations()
        assert result is True
        assert mock_run.call_count == 2


@pytest.mark.template_only
class TestVerifySetupScript:
    """Test the verification script functionality."""

    @patch("os.getenv")
    def test_verify_script_checks_environment_variables(self, mock_getenv):
        """Test that the verification script checks environment variables."""
        # Mock environment variables
        mock_getenv.side_effect = lambda var: {
            "DATABASE_URL": "postgresql://test",
            "SECRET_KEY": "test_key",
            "POSTGRES_DB": "test_db",
            "POSTGRES_USER": "test_user",
            "POSTGRES_PASSWORD": "test_pass",
            "POSTGRES_PORT": "5432",
            "API_PORT": "8000",
            "ENABLE_REDIS": "false",
            "ENABLE_CELERY": "false",
            "BACKEND_CORS_ORIGINS": '["http://localhost:3000"]',
            "FIRST_SUPERUSER": None,
            "FIRST_SUPERUSER_PASSWORD": None,
        }.get(var)

        from scripts.verify_setup import check_environment_variables

        result = check_environment_variables()

        # Check that all required variables are marked as set
        assert all(result["required"].values())
        # Check that optional variables are handled
        assert "ENABLE_REDIS" in result["optional"]

    def test_verify_script_checks_database_connection(self):
        """Test that the verification script checks database connectivity."""
        # Mock successful database connection
        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value = MagicMock()

        # Mock the import inside the function
        with patch("app.database.database.engine", mock_engine):
            from scripts.verify_setup import check_database_connection

            result = check_database_connection()
            assert result is True

    def test_verify_script_handles_database_connection_failure(self):
        """Test that the verification script handles database connection failures."""
        # Mock database connection failure
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = Exception("Connection failed")

        # Mock the import inside the function
        with patch("app.database.database.engine", mock_engine):
            from scripts.verify_setup import check_database_connection

            result = check_database_connection()
            assert result is False

    @patch("subprocess.run")
    def test_verify_script_checks_docker_services(self, mock_run):
        """Test that the verification script checks Docker services."""
        # Mock Docker services status
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "postgres   Up"

        from scripts.verify_setup import check_docker_services

        result = check_docker_services()
        assert "postgres" in result
        assert result["postgres"] is True

    @patch("subprocess.run")
    def test_verify_script_handles_docker_not_running(self, mock_run):
        """Test that the verification script handles Docker services not running."""
        # Mock Docker service not running
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "postgres   Exit"

        from scripts.verify_setup import check_docker_services

        result = check_docker_services()
        assert "postgres" in result
        assert result["postgres"] is False

    @patch("pathlib.Path.exists")
    def test_verify_script_checks_file_structure(self, mock_exists):
        """Test that the verification script checks file structure."""
        # Mock file existence
        mock_exists.side_effect = lambda: True

        from scripts.verify_setup import check_file_structure

        result = check_file_structure()
        assert "files" in result
        assert "directories" in result
        assert all(result["files"].values())
        assert all(result["directories"].values())


@pytest.mark.template_only
class TestFixCommonIssuesScript:
    """Test the fix common issues script functionality."""

    def test_fix_script_creates_env_file_when_missing(self):
        """Test that the fix script creates .env file when missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"

            # Test creating .env file
            from scripts.fix_common_issues import create_env_file

            create_env_file(env_path)

            assert env_path.exists()
            content = env_path.read_text()

            # Check for required Docker variables
            assert "POSTGRES_DB=fastapi_template" in content
            assert "POSTGRES_USER=postgres" in content
            assert "POSTGRES_PASSWORD=dev_password_123" in content
            assert "POSTGRES_PORT=5432" in content
            assert "REDIS_PORT=6379" in content
            assert "API_PORT=8000" in content

    def test_fix_script_adds_missing_docker_variables(self):
        """Test that the fix script adds missing Docker variables to existing .env."""
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"

            # Create minimal .env file
            env_path.write_text("DATABASE_URL=postgresql://test\n")

            from scripts.fix_common_issues import add_missing_docker_variables

            add_missing_docker_variables(env_path)

            content = env_path.read_text()

            # Check that Docker variables were added
            assert "POSTGRES_DB=fastapi_template" in content
            assert "POSTGRES_USER=postgres" in content
            assert "POSTGRES_PORT=5432" in content

    def test_fix_script_converts_cors_format(self):
        """Test that the fix script converts CORS format from comma-separated to JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"

            # Create .env with wrong CORS format
            env_path.write_text(
                "BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8080\n"
            )

            from scripts.fix_common_issues import fix_cors_format

            fix_cors_format(env_path)

            content = env_path.read_text()

            # Check that CORS format was converted (with spaces as json.dumps adds them)
            assert (
                'BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]'
                in content
            )

    def test_fix_script_handles_correct_cors_format(self):
        """Test that the fix script doesn't change already correct CORS format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"

            # Create .env with correct CORS format
            original_content = 'BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]\n'
            env_path.write_text(original_content)

            from scripts.fix_common_issues import fix_cors_format

            fix_cors_format(env_path)

            content = env_path.read_text()

            # Check that CORS format wasn't changed
            assert content == original_content

    @patch("pathlib.Path.exists")
    def test_fix_script_validates_alembic_config(self, mock_exists):
        """Test that the fix script validates alembic.ini configuration."""
        # Mock alembic.ini exists
        mock_exists.return_value = True

        with tempfile.TemporaryDirectory() as temp_dir:
            alembic_path = Path(temp_dir) / "alembic.ini"

            # Create alembic.ini with proper configuration
            alembic_path.write_text(
                """
[alembic]
script_location = alembic
sqlalchemy.url = postgresql://postgres:dev_password_123@localhost:5432/fastapi_template
"""
            )

            from scripts.fix_common_issues import validate_alembic_config

            result = validate_alembic_config(alembic_path)
            assert result is True

    def test_fix_script_creates_alembic_config_when_missing(self):
        """Test that the fix script creates alembic.ini when missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            alembic_path = Path(temp_dir) / "alembic.ini"

            # Verify file doesn't exist initially
            assert not alembic_path.exists()

            from scripts.fix_common_issues import create_alembic_config

            create_alembic_config(alembic_path)

            # Verify file was created
            assert alembic_path.exists()
            content = alembic_path.read_text()

            # Check for required configuration
            assert "[alembic]" in content
            assert "script_location = alembic" in content
            assert "sqlalchemy.url = postgresql://" in content


@pytest.mark.template_only
class TestScriptIntegration:
    """Integration tests for the setup scripts."""

    @patch("subprocess.run")
    @patch("os.getenv")
    def test_full_setup_workflow(self, mock_getenv, mock_run):
        """Test the complete setup workflow."""
        # Mock environment variables
        mock_getenv.side_effect = lambda var: {
            "DATABASE_URL": "postgresql://test",
            "SECRET_KEY": "test_key",
            "POSTGRES_DB": "test_db",
            "POSTGRES_USER": "test_user",
            "POSTGRES_PASSWORD": "test_pass",
            "POSTGRES_PORT": "5432",
            "API_PORT": "8000",
        }.get(var, None)

        # Mock successful subprocess calls
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "postgres   Up"

        with tempfile.TemporaryDirectory() as temp_dir:
            # Test setup workflow
            from scripts.setup_comprehensive import run_setup_workflow

            # Mock database connection for verification
            mock_conn = MagicMock()
            mock_engine = MagicMock()
            mock_engine.connect.return_value.__enter__.return_value = mock_conn
            mock_conn.execute.return_value = MagicMock()

            with patch("app.database.database.engine", mock_engine):
                from scripts.verify_setup import run_verification

                # Run setup
                setup_result = run_setup_workflow(Path(temp_dir))
                assert setup_result is True

                # Run verification
                verify_result = run_verification()
                assert verify_result is True

    def test_script_error_handling(self):
        """Test that scripts handle errors gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test with invalid paths
            invalid_path = Path(temp_dir) / "nonexistent" / "file.txt"

            from scripts.verify_setup import check_file_exists

            result = check_file_exists(str(invalid_path), "Test file")
            assert result is False


# Test data for parametrized tests
@pytest.mark.template_only
@pytest.mark.parametrize(
    "env_var,expected",
    [
        ("DATABASE_URL", True),
        ("SECRET_KEY", True),
        ("NONEXISTENT_VAR", False),
    ],
)
def test_environment_variable_checking(env_var, expected):
    """Test environment variable checking with different variables."""
    with patch("os.getenv") as mock_getenv:
        mock_getenv.return_value = "test_value" if expected else None

        from scripts.verify_setup import check_environment_variable

        result = check_environment_variable(env_var)
        assert result == expected


@pytest.mark.template_only
@pytest.mark.parametrize(
    "cors_input,expected",
    [
        (
            "http://localhost:3000,http://localhost:8080",
            '["http://localhost:3000", "http://localhost:8080"]',
        ),
        (
            '["http://localhost:3000","http://localhost:8080"]',
            '["http://localhost:3000","http://localhost:8080"]',
        ),
        ("http://localhost:3000", '["http://localhost:3000"]'),
        ("", "[]"),
    ],
)
def test_cors_format_conversion(cors_input, expected):
    """Test CORS format conversion with various inputs."""
    from scripts.fix_common_issues import convert_cors_format

    result = convert_cors_format(cors_input)
    assert result == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
