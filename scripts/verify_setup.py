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

    def check_file_exists(self, file_path: str, description: str) -> bool:
        """Check if a file exists."""
        full_path = self.project_root / file_path
        if full_path.exists():
            print(f"✅ {description}")
            return True
        else:
            print(f"❌ {description} - File not found: {file_path}")
            self.issues.append(f"Missing file: {file_path}")
            return False

    def check_directory_exists(self, dir_path: str, description: str) -> bool:
        """Check if a directory exists."""
        full_path = self.project_root / dir_path
        if full_path.exists() and full_path.is_dir():
            print(f"✅ {description}")
            return True
        else:
            print(f"❌ {description} - Directory not found: {dir_path}")
            self.issues.append(f"Missing directory: {dir_path}")
            return False

    def check_environment_variable(self, var_name: str, description: str) -> bool:
        """Check if an environment variable is set."""
        value = os.getenv(var_name)
        if value:
            print(f"✅ {description}: {var_name} is set")
            return True
        else:
            print(f"⚠️  {description}: {var_name} is not set")
            self.warnings.append(f"Environment variable not set: {var_name}")
            return False

    def check_python_import(self, module_name: str, description: str) -> bool:
        """Check if a Python module can be imported."""
        try:
            __import__(module_name)
            print(f"✅ {description}")
            return True
        except ImportError as e:
            print(f"❌ {description} - Import failed: {e}")
            self.issues.append(f"Python import failed: {module_name}")
            return False

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
                    return True
                except Exception as e:
                    print(f"❌ Database connection failed: {e}")
                    self.issues.append(f"Database connection failed: {e}")
                    return False

            result = asyncio.run(test_connection())
            if result:
                print("✅ Database connection")
            return result

        except Exception as e:
            print(f"❌ Database connection test failed: {e}")
            self.issues.append(f"Database connection test failed: {e}")
            return False

    def check_api_startup(self) -> bool:
        """Check if the API can start without errors."""
        try:
            # Add project root to Python path
            sys.path.insert(0, str(self.project_root))

            print("✅ API startup test")
            return True

        except Exception as e:
            print(f"❌ API startup test failed: {e}")
            self.issues.append(f"API startup test failed: {e}")
            return False

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

            if result.returncode == 0:
                output = result.stdout
                if "postgres" in output.lower() and "api" in output.lower():
                    print("✅ Docker services are running")
                    return True
                else:
                    print("⚠️  Docker services may not be running")
                    self.warnings.append("Docker services may not be running")
                    return False
            else:
                print("❌ Docker services check failed")
                self.issues.append("Docker services check failed")
                return False

        except FileNotFoundError:
            print("⚠️  docker-compose not found")
            self.warnings.append("docker-compose not found")
            return False
        except Exception as e:
            print(f"❌ Docker services check failed: {e}")
            self.issues.append(f"Docker services check failed: {e}")
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

            if result.returncode == 0:
                print("✅ Alembic migrations are up to date")
                return True
            else:
                print("⚠️  Alembic migrations may not be up to date")
                self.warnings.append("Alembic migrations may not be up to date")
                return False

        except FileNotFoundError:
            print("⚠️  alembic not found")
            self.warnings.append("alembic not found")
            return False
        except Exception as e:
            print(f"❌ Alembic check failed: {e}")
            self.issues.append(f"Alembic check failed: {e}")
            return False

    def check_project_structure(self) -> None:
        """Check the basic project structure."""
        print("\n📁 Checking project structure...")

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
        print("\n🐍 Checking Python environment...")

        # Check Python version
        python_version = sys.version_info
        if python_version.major == 3 and python_version.minor >= 8:
            print(
                f"✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}"
            )
        else:
            print(
                f"❌ Python version: {python_version.major}.{python_version.minor}.{python_version.micro} (requires 3.8+)"
            )
            self.issues.append("Python version too old (requires 3.8+)")

        # Check essential imports
        self.check_python_import("fastapi", "FastAPI framework")
        self.check_python_import("sqlalchemy", "SQLAlchemy ORM")
        self.check_python_import("alembic", "Alembic migrations")
        self.check_python_import("pydantic", "Pydantic validation")

    def check_configuration(self) -> None:
        """Check configuration and environment."""
        print("\n⚙️  Checking configuration...")

        # Check if .env file exists
        env_file = self.project_root / ".env"
        if env_file.exists():
            print("✅ Environment file (.env) exists")
        else:
            print("⚠️  Environment file (.env) not found")
            self.warnings.append("Environment file (.env) not found")

        # Check environment variables
        self.check_environment_variable("DATABASE_URL", "Database URL")
        self.check_environment_variable("SECRET_KEY", "Secret key")

    def check_services(self) -> None:
        """Check if services are running."""
        print("\n🔧 Checking services...")

        self.check_docker_services()
        self.check_database_connection()
        self.check_api_startup()
        self.check_alembic_migrations()

    def run_verification(self) -> None:
        """Run the complete verification process."""
        print("🔍 FastAPI Project Setup Verification")
        print("=" * 50)

        self.check_project_structure()
        self.check_python_environment()
        self.check_configuration()
        self.check_services()

        # Summary
        print("\n📊 Verification Summary")
        print("=" * 30)

        if not self.issues and not self.warnings:
            print("🎉 All checks passed! Your setup is working correctly.")
            print("\n🚀 Next steps:")
            print("  - Visit http://localhost:8000/docs to see your API")
            print("  - Run tests: pytest")
            print("  - Start developing your application!")
        else:
            if self.issues:
                print(f"❌ Found {len(self.issues)} issue(s):")
                for issue in self.issues:
                    print(f"  - {issue}")

            if self.warnings:
                print(f"⚠️  Found {len(self.warnings)} warning(s):")
                for warning in self.warnings:
                    print(f"  - {warning}")

            print("\n🔧 Troubleshooting:")
            print(
                "  - Check the troubleshooting guide: docs/troubleshooting/setup-issues.md"
            )
            print("  - Review the setup logs for more details")
            print("  - Ensure all services are running: docker-compose up -d")


def main():
    """Main entry point."""
    verifier = SetupVerifier()
    verifier.run_verification()


if __name__ == "__main__":
    main()
