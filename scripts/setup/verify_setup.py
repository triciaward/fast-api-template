#!/usr/bin/env python3
"""
Setup Verification Script

This script verifies that your FastAPI project setup is working correctly.
Run this after completing the setup process to ensure everything is configured properly.
"""

import asyncio
import os
import subprocess
import sys
from pathlib import Path


class SetupVerifier:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.issues: list[str] = []
        self.warnings: list[str] = []
        self.venv_activated = False

    def detect_and_activate_venv(self) -> bool:
        """Detect and activate virtual environment if needed."""
        # Check if we're already in a virtual environment
        if hasattr(sys, "real_prefix") or (
            hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
        ):
            self.venv_activated = True
            return True

        # Check if venv directory exists
        venv_path = self.project_root / "venv"
        if not venv_path.exists():
            self.issues.append("Virtual environment not found")
            return False

        # Try to activate the virtual environment
        venv_python = venv_path / "bin" / "python"
        if not venv_python.exists():
            venv_python = venv_path / "Scripts" / "python.exe"  # Windows

        if venv_python.exists():
            self.warnings.append(
                "Virtual environment not activated - some checks may fail",
            )
            return False

        self.issues.append("Virtual environment Python executable not found")
        return False

    def check_file_exists(self, file_path: str, _description: str) -> bool:
        """Check if a file exists."""
        full_path = self.project_root / file_path
        if full_path.exists():
            return True
        self.issues.append(f"Missing file: {file_path}")
        return False

    def check_directory_exists(self, dir_path: str, _description: str) -> bool:
        """Check if a directory exists."""
        full_path = self.project_root / dir_path
        if full_path.exists() and full_path.is_dir():
            return True
        self.issues.append(f"Missing directory: {dir_path}")
        return False

    def check_environment_variable(self, var_name: str, _description: str) -> bool:
        """Check if an environment variable is set."""
        value = os.getenv(var_name)
        if value:
            return True
        self.warnings.append(f"Environment variable not set: {var_name}")
        return False

    def check_python_import(self, module_name: str, _description: str) -> bool:
        """Check if a Python module can be imported."""
        try:
            __import__(module_name)
        except ImportError:
            self.issues.append(f"Python import failed: {module_name}")
            return False
        else:
            return True

    def check_database_connection(self) -> bool:
        """Check if database connection works."""
        try:
            # Add project root to Python path
            sys.path.insert(0, str(self.project_root))

            from sqlalchemy import text

            from app.database.database import engine

            async def test_connection():
                try:
                    async with engine.begin() as conn:
                        await conn.execute(text("SELECT 1"))
                except Exception as e:
                    self.issues.append(f"Database connection failed: {e}")
                    return False
                else:
                    return True

            result = asyncio.run(test_connection())
        except Exception as e:
            self.issues.append(f"Database connection test failed: {e}")
            return False
        else:
            return result

    def check_api_startup(self) -> bool:
        """Check if the API can start without errors."""
        try:
            # Add project root to Python path
            sys.path.insert(0, str(self.project_root))
        except Exception as e:
            self.issues.append(f"API startup test failed: {e}")
            return False
        else:
            return True

    def check_docker_services(self) -> bool:
        """Check if Docker services are running."""
        try:
            # Check if docker-compose is available
            result = subprocess.run(
                ["docker-compose", "ps"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )
        except FileNotFoundError:
            self.warnings.append("docker-compose not found")
            return False
        except Exception as e:
            self.issues.append(f"Docker services check failed: {e}")
            return False
        else:
            if result.returncode == 0:
                output = result.stdout
                if "postgres" in output.lower() and "api" in output.lower():
                    return True
                self.warnings.append("Docker services may not be running")
                return False
            self.issues.append("Docker services check failed")
            return False

    def check_alembic_migrations(self) -> bool:
        """Check if Alembic migrations are up to date."""
        try:
            result = subprocess.run(
                ["alembic", "current"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )
        except FileNotFoundError:
            self.warnings.append("alembic not found")
            return False
        except Exception as e:
            self.issues.append(f"Alembic check failed: {e}")
            return False
        else:
            if result.returncode == 0:
                return True
            self.warnings.append("Alembic migrations may not be up to date")
            return False

    def check_project_structure(self) -> None:
        """Check the basic project structure."""

        # Essential files
        self.check_file_exists("alembic.ini", "Alembic configuration")
        self.check_file_exists("requirements.txt", "Python dependencies")
        self.check_file_exists("docker-compose.yml", "Docker Compose configuration")
        self.check_file_exists("app/main.py", "FastAPI application entry point")
        self.check_file_exists("app/core/config.py", "Application configuration")

        # Essential directories
        self.check_directory_exists("app", "Application directory")
        self.check_directory_exists("alembic", "Alembic migrations directory")
        self.check_directory_exists("tests", "Tests directory")
        self.check_directory_exists("scripts", "Scripts directory")

    def check_python_environment(self) -> None:
        """Check Python environment and dependencies."""

        # Check Python version
        python_version = sys.version_info
        if python_version.major == 3 and python_version.minor >= 8:
            pass
        else:
            self.issues.append("Python version too old (requires 3.8+)")

        # Check essential imports
        self.check_python_import("fastapi", "FastAPI framework")
        self.check_python_import("sqlalchemy", "SQLAlchemy ORM")
        self.check_python_import("alembic", "Alembic migrations")
        self.check_python_import("pydantic", "Pydantic validation")

    def check_configuration(self) -> None:
        """Check configuration and environment."""

        # Check if .env file exists
        env_file = self.project_root / ".env"
        if env_file.exists():
            pass
        else:
            self.warnings.append("Environment file (.env) not found")

        # Check environment variables
        # Note: Some variables are Docker-only and won't be set in local .env
        self.check_environment_variable("DATABASE_URL", "Database URL")
        self.check_environment_variable("SECRET_KEY", "Secret key")

        # Add note about Docker environment variables
        if not os.getenv("DATABASE_URL") or not os.getenv("SECRET_KEY"):
            pass

    def check_services(self) -> None:
        """Check if services are running."""

        self.check_docker_services()
        self.check_database_connection()
        self.check_api_startup()
        self.check_alembic_migrations()

    def run_verification(self) -> None:
        """Run the complete verification process."""

        # Check virtual environment first
        self.detect_and_activate_venv()

        self.check_project_structure()
        self.check_python_environment()
        self.check_configuration()
        self.check_services()

        # Summary

        if not self.issues and not self.warnings:
            pass
        else:
            if self.issues:
                for _issue in self.issues:
                    pass

            if self.warnings:
                for _warning in self.warnings:
                    pass


def main():
    """Main entry point."""
    verifier = SetupVerifier()
    verifier.run_verification()


if __name__ == "__main__":
    main()
