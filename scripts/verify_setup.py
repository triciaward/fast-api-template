#!/usr/bin/env python3
"""
FastAPI Template Setup Verification Script

This script verifies that your FastAPI Template setup is working correctly
by testing various components and providing detailed feedback.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def print_header(title: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"✅ {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    print(f"❌ {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    print(f"⚠️  {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    print(f"ℹ️  {message}")


def check_file_exists(file_path: str, description: str) -> bool:
    """Check if a file exists and print result."""
    if Path(file_path).exists():
        print_success(f"{description}: {file_path}")
        return True
    else:
        print_error(f"{description}: {file_path} (not found)")
        return False


def check_environment_variable(var_name: str) -> bool:
    """Check if a single environment variable is set."""
    return os.getenv(var_name) is not None


def check_environment_variables() -> dict[str, Any]:
    """Check required environment variables."""
    print_header("Environment Variables Check")

    required_vars = [
        "DATABASE_URL",
        "SECRET_KEY",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_PORT",
        "API_PORT",
    ]

    optional_vars = [
        "ENABLE_REDIS",
        "ENABLE_CELERY",
        "ENABLE_WEBSOCKETS",
        "BACKEND_CORS_ORIGINS",
        "FIRST_SUPERUSER",
        "FIRST_SUPERUSER_PASSWORD",
    ]

    results: dict[str, dict[str, bool]] = {"required": {}, "optional": {}}

    # Check required variables
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print_success(f"{var}: Set")
            results["required"][var] = True
        else:
            print_error(f"{var}: Not set")
            results["required"][var] = False

    # Check optional variables
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print_success(f"{var}: Set ({value})")
            results["optional"][var] = True
        else:
            print_info(f"{var}: Not set (optional)")
            results["optional"][var] = False

    return results


async def check_database_connection() -> bool:
    """Test database connection."""
    print_header("Database Connection Test")

    try:
        from sqlalchemy import text

        from app.database.database import engine

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            print_success("Database connection successful")
            return True
    except Exception as e:
        print_error(f"Database connection failed: {e}")
        return False


def check_configuration_loading() -> bool:
    """Test configuration loading."""
    print_header("Configuration Loading Test")

    try:
        from app.core.config import settings

        print_success("Configuration loaded successfully")
        print_info(f"Environment: {settings.ENVIRONMENT}")
        print_info(f"Database URL: {settings.DATABASE_URL}")
        print_info(f"CORS Origins: {settings.BACKEND_CORS_ORIGINS}")

        return True
    except Exception as e:
        print_error(f"Configuration loading failed: {e}")
        return False


def check_alembic_migrations() -> bool:
    """Check Alembic migration status."""
    print_header("Database Migrations Check")

    try:
        result = subprocess.run(
            ["alembic", "current"], capture_output=True, text=True, cwd=project_root
        )

        if result.returncode == 0:
            print_success("Alembic migrations are up to date")
            print_info(f"Current migration: {result.stdout.strip()}")
            return True
        else:
            print_warning("Alembic migration status unclear")
            print_info(f"Output: {result.stderr}")
            return False
    except Exception as e:
        print_error(f"Failed to check migrations: {e}")
        return False


def check_docker_services() -> dict[str, bool]:
    """Check Docker services status."""
    print_header("Docker Services Check")

    services = ["postgres", "redis"]
    results = {}

    try:
        for service in services:
            result = subprocess.run(
                ["docker-compose", "ps", service],
                capture_output=True,
                text=True,
                cwd=project_root,
            )

            if result.returncode == 0 and "Up" in result.stdout:
                print_success(f"{service}: Running")
                results[service] = True
            else:
                print_warning(f"{service}: Not running")
                results[service] = False

    except Exception as e:
        print_error(f"Failed to check Docker services: {e}")
        results = {service: False for service in services}

    return results


def check_api_endpoints() -> bool:
    """Test basic API functionality."""
    print_header("API Endpoints Test")

    try:
        import requests

        # Start the API server in background (if not already running)
        print_info("Testing API endpoints...")

        # Test health endpoint
        try:
            response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
            if response.status_code == 200:
                print_success("Health endpoint: Working")
                health_data = response.json()
                print_info(f"Status: {health_data.get('status', 'unknown')}")
                return True
            else:
                print_warning(f"Health endpoint returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print_warning(
                "API server not running. Start with: uvicorn app.main:app --reload"
            )
            return False
        except Exception as e:
            print_error(f"API test failed: {e}")
            return False

    except ImportError:
        print_warning(
            "requests library not available. Install with: pip install requests"
        )
        return False


def check_file_structure() -> dict[str, dict[str, bool]]:
    """Check important files and directories."""
    print_header("File Structure Check")

    important_files = [
        ("alembic.ini", "Alembic configuration"),
        ("docker-compose.yml", "Docker Compose configuration"),
        ("requirements.txt", "Python dependencies"),
        ("app/main.py", "FastAPI application entry point"),
        ("app/core/config.py", "Application configuration"),
        ("app/database/database.py", "Database configuration"),
        ("app/bootstrap_superuser.py", "Superuser bootstrap script"),
    ]

    important_dirs = [
        ("alembic/", "Alembic migrations directory"),
        ("app/", "Application source code"),
        ("tests/", "Test files"),
        ("docs/", "Documentation"),
    ]

    results: dict[str, dict[str, bool]] = {"files": {}, "directories": {}}

    # Check files
    for file_path, description in important_files:
        exists = check_file_exists(file_path, description)
        results["files"][file_path] = exists

    # Check directories
    for dir_path, description in important_dirs:
        exists = Path(dir_path).exists()
        if exists:
            print_success(f"{description}: {dir_path}")
        else:
            print_error(f"{description}: {dir_path} (not found)")
        results["directories"][dir_path] = exists

    return results


def generate_summary_report(
    env_vars: dict[str, Any],
    db_connection: bool,
    config_loading: bool,
    migrations: bool,
    docker_services: dict[str, bool],
    api_endpoints: bool,
    file_structure: dict[str, dict[str, bool]],
) -> None:
    """Generate a summary report."""
    print_header("Setup Verification Summary")

    # Calculate success rates
    required_env_vars_ok = all(env_vars["required"].values())
    files_ok = all(file_structure["files"].values())
    docker_ok = any(docker_services.values())

    # Overall status
    critical_issues = []
    warnings = []

    if not required_env_vars_ok:
        critical_issues.append("Missing required environment variables")

    if not db_connection:
        critical_issues.append("Database connection failed")

    if not config_loading:
        critical_issues.append("Configuration loading failed")

    if not files_ok:
        critical_issues.append("Missing critical files")

    if not docker_ok:
        warnings.append("Docker services not running")

    if not api_endpoints:
        warnings.append("API server not accessible")

    # Print summary
    if not critical_issues:
        print_success("🎉 Setup verification PASSED!")
        print_info("Your FastAPI Template is ready for development.")
    else:
        print_error("❌ Setup verification FAILED!")
        print_info("Please address the critical issues below:")
        for issue in critical_issues:
            print_error(f"  - {issue}")

    if warnings:
        print_warning("⚠️  Warnings (non-critical):")
        for warning in warnings:
            print_warning(f"  - {warning}")

    # Next steps
    print_header("Next Steps")
    if not critical_issues:
        print_success("1. Start the development server:")
        print("   uvicorn app.main:app --reload")
        print()
        print_success("2. Access your API:")
        print("   - API: http://localhost:8000")
        print("   - Docs: http://localhost:8000/docs")
        print("   - ReDoc: http://localhost:8000/redoc")
        print()
        print_success("3. Create a superuser (optional):")
        print("   python app/bootstrap_superuser.py")
    else:
        print_error("Please fix the critical issues above before proceeding.")
        print_info("Run the comprehensive setup script:")
        print("   ./scripts/setup_comprehensive.sh")


async def run_verification() -> bool:
    """Run the complete verification process."""
    try:
        # Run all checks
        env_vars = check_environment_variables()
        db_connection = await check_database_connection()
        config_loading = check_configuration_loading()
        migrations = check_alembic_migrations()
        docker_services = check_docker_services()
        api_endpoints = check_api_endpoints()
        file_structure = check_file_structure()

        # Generate summary
        generate_summary_report(
            env_vars=env_vars,
            db_connection=db_connection,
            config_loading=config_loading,
            migrations=migrations,
            docker_services=docker_services,
            api_endpoints=api_endpoints,
            file_structure=file_structure,
        )

        # Return success if no critical issues
        required_env_vars_ok = all(env_vars["required"].values())
        files_ok = all(file_structure["files"].values())

        return required_env_vars_ok and db_connection and config_loading and files_ok

    except Exception as e:
        print_error(f"Verification failed with error: {e}")
        return False


async def main():
    """Main verification function."""
    print("FastAPI Template Setup Verification")
    print("===================================")

    success = await run_verification()
    return 0 if success else 1


if __name__ == "__main__":
    import asyncio

    exit(asyncio.run(main()))
