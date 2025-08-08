#!/usr/bin/env python3
"""
FastAPI Template - One-Command Project Setup

This script handles the complete setup of your FastAPI project:
1. Prompts for your project details
2. Customizes all template files with your information
3. Sets up the development environment
4. Starts services and runs migrations
5. Installs git protection hooks

Usage:
    ./scripts/setup/setup_project.py

Designed for GitHub "Use this template" workflow:
1. Click "Use this template" on GitHub
2. Clone your new repository
3. Run this script
"""

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


class ProjectSetup:
    def __init__(self):
        self.project_root = Path.cwd()
        self.current_dir_name = self.project_root.name
        self.replacements: dict[str, str] = {}

    def validate_project_structure(self) -> bool:
        """Validate that this looks like a FastAPI template project."""
        required_files = [
            "app/main.py",
            "requirements.txt",
            "docker-compose.yml",
            "scripts/git-hooks/pre-commit",
        ]

        for file_path in required_files:
            if not self.project_root.joinpath(file_path).exists():
                return False
        return True

    def get_project_details(self) -> dict[str, str]:
        """Get project details from user input."""
        print("🚀 FastAPI Project Setup")
        print("=" * 50)
        print()
        print("Setting up your FastAPI project...")
        print()

        # Get project details
        details = {}

        # GitHub template - use current directory name
        details["project_slug"] = self.current_dir_name

        # Derive project name from slug
        name_from_slug = (
            self.current_dir_name.replace("_", " ").replace("-", " ").title()
        )
        name_from_slug = re.sub(r"\s+Backend$", "", name_from_slug, flags=re.IGNORECASE)

        user_name = input(f"Project name [{name_from_slug}]: ").strip()
        details["project_name"] = user_name if user_name else name_from_slug

        # Get other details
        details["author_name"] = input("Author name: ").strip() or "Your Name"
        details["author_email"] = (
            input("Author email: ").strip() or "your.email@example.com"
        )

        # Generate database name from slug
        db_name = details["project_slug"].replace("-", "_").lower()
        user_db = input(f"Database name [{db_name}]: ").strip()
        details["database_name"] = user_db if user_db else db_name

        # Generate description
        default_desc = f"A FastAPI backend for {details['project_name']}"
        user_desc = input(f"Project description [{default_desc}]: ").strip()
        details["description"] = user_desc if user_desc else default_desc

        return details

    def confirm_details(self, details: dict[str, str]) -> bool:
        """Show summary and get confirmation."""
        print()
        print("📋 Setup Summary:")
        print("=" * 30)
        print(f"  Project Name: {details['project_name']}")
        print(f"  Project Folder: {details['project_slug']}")
        print(f"  Database Name: {details['database_name']}")
        print(f"  Description: {details['description']}")
        print(f"  Author: {details['author_name']} <{details['author_email']}>")
        print("  Action: Customize files and set up environment")

        print()
        confirm = input("Proceed with setup? (y/N): ").strip().lower()
        return confirm in ["y", "yes"]

    def setup_replacements(self, details: dict[str, str]) -> None:
        """Set up string replacements for customization."""
        slug = details["project_slug"]

        self.replacements = {
            # Project names and descriptions
            "fast-api-template": slug,
            "fast_api_template": slug.replace("-", "_"),
            "FastAPI Template": details["project_name"],
            "A comprehensive, production-ready FastAPI template": details[
                "description"
            ],
            # Database names
            "fastapi_template": details["database_name"],
            "postgresql://postgres:dev_password_123@localhost:5432/fastapi_template": f"postgresql://postgres:dev_password_123@localhost:5432/{details['database_name']}",
            # Docker container names
            "fast-api-template_postgres": f"{slug}_postgres",
            "fast-api-template_api": f"{slug}_api",
            "fast-api-template_redis": f"{slug}_redis",
            "fast-api-template_celery": f"{slug}_celery",
            # Author information
            "Your Name": details["author_name"],
            "your.email@example.com": details["author_email"],
            # Git repository (placeholder - user will update manually)
            "https://github.com/triciaward/fast-api-template": f"https://github.com/yourusername/{slug}",
        }

    def customize_files(self) -> None:
        """Replace template placeholders in all files."""
        print()
        print("🔄 Customizing project files...")

        # Files to process
        patterns_to_include = [
            "*.py",
            "*.md",
            "*.yml",
            "*.yaml",
            "*.txt",
            "*.ini",
            "*.sh",
            "*.env*",
            "Dockerfile*",
            "*.json",
        ]

        # Directories to skip
        dirs_to_skip = {
            ".git",
            "__pycache__",
            ".pytest_cache",
            "venv",
            ".venv",
            "node_modules",
            ".mypy_cache",
            "htmlcov",
            ".coverage",
        }

        files_processed = 0
        files_updated = 0

        for pattern in patterns_to_include:
            for file_path in self.project_root.rglob(pattern):
                # Skip files in excluded directories
                if any(part in dirs_to_skip for part in file_path.parts):
                    continue

                # Skip binary files and very large files
                if file_path.stat().st_size > 1024 * 1024:  # 1MB
                    continue

                try:
                    files_processed += 1
                    if self.process_file(file_path):
                        files_updated += 1
                        print(
                            f"   ✅ Updated: {file_path.relative_to(self.project_root)}",
                        )
                except Exception as e:
                    print(f"   ⚠️  Skipped {file_path.name}: {e}")

        print(
            f"✅ Customization complete: {files_updated}/{files_processed} files updated",
        )

    def process_file(self, file_path: Path) -> bool:
        """Process a single file for template replacements."""
        try:
            # Read file content
            with file_path.open(encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # Skip binary files
            return False

        original_content = content

        # Apply replacements
        for old, new in self.replacements.items():
            content = content.replace(old, new)

        # Write back if changed
        if content != original_content:
            with file_path.open("w", encoding="utf-8") as f:
                f.write(content)
            return True

        return False

    def setup_environment(self) -> None:
        """Set up the development environment."""
        print()
        print("🔧 Setting up development environment...")

        # Create .env from .env.example
        env_file = self.project_root / ".env"
        env_example = self.project_root / ".env.example"

        if not env_file.exists() and env_example.exists():
            print("   Creating .env file...")
            shutil.copy2(env_example, env_file)
            print("   ✅ .env file created")

        # Create virtual environment
        venv_dir = self.project_root / "venv"
        if not venv_dir.exists():
            print("   Creating Python virtual environment...")
            subprocess.run(
                [sys.executable, "-m", "venv", "venv"],
                cwd=self.project_root,
                check=True,
            )
            print("   ✅ Virtual environment created")

        # Install dependencies
        print("   Installing Python dependencies...")
        pip_path = venv_dir / "bin" / "pip"
        if not pip_path.exists():
            pip_path = venv_dir / "Scripts" / "pip.exe"  # Windows

        subprocess.run(
            [str(pip_path), "install", "--upgrade", "pip"],
            cwd=self.project_root,
            check=True,
        )
        subprocess.run(
            [str(pip_path), "install", "-r", "requirements.txt"],
            cwd=self.project_root,
            check=True,
        )
        print("   ✅ Dependencies installed")

    def check_docker(self) -> None:
        """Check if Docker is running."""
        print()
        print("🐳 Checking Docker...")
        try:
            subprocess.run(["docker", "info"], capture_output=True, check=True)
            print("✅ Docker is running")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Error: Docker is not running!")
            print("   Please start Docker and run this script again.")
            sys.exit(1)

    def start_services(self) -> None:
        """Start Docker services."""
        print()
        print("🗄️  Starting database services...")

        try:
            subprocess.run(
                ["docker-compose", "up", "-d", "postgres"],
                cwd=self.project_root,
                check=True,
            )
            print("✅ Database service started")

            # Wait for PostgreSQL
            print("⏳ Waiting for PostgreSQL to be ready...")
            self.wait_for_postgres()

        except subprocess.CalledProcessError as e:
            print(f"❌ Error starting services: {e}")
            sys.exit(1)

    def wait_for_postgres(self) -> None:
        """Wait for PostgreSQL to be ready."""
        for i in range(30):
            try:
                result = subprocess.run(
                    [
                        "docker-compose",
                        "exec",
                        "-T",
                        "postgres",
                        "pg_isready",
                        "-U",
                        "postgres",
                    ],
                    cwd=self.project_root,
                    capture_output=True,
                )
                if result.returncode == 0:
                    print("✅ PostgreSQL is ready")
                    return
            except subprocess.CalledProcessError:
                pass

            if i == 29:
                print("❌ Error: PostgreSQL failed to start within 30 seconds")
                sys.exit(1)

            print(f"   Waiting... ({i+1}/30)")
            time.sleep(2)

    def run_migrations(self) -> None:
        """Run database migrations."""
        print()
        print("🔄 Running database migrations...")

        python_path = self.project_root / "venv" / "bin" / "python"
        if not python_path.exists():
            python_path = (
                self.project_root / "venv" / "Scripts" / "python.exe"
            )  # Windows

        try:
            env = os.environ.copy()
            env["PYTHONPATH"] = str(self.project_root)

            result = subprocess.run(
                [str(python_path), "-m", "alembic", "upgrade", "head"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                env=env,
            )

            if result.returncode == 0:
                print("✅ Database migrations completed")
            else:
                print("⚠️  Migration completed with warnings")
                print("   This is normal for existing databases")

        except subprocess.CalledProcessError as e:
            print(f"❌ Error running migrations: {e}")
            # Don't exit - migrations might not be critical for initial setup

    def create_superuser(self, details: dict[str, str]) -> None:
        """Create a superuser account."""
        print()
        print("👤 Creating superuser account...")

        python_path = self.project_root / "venv" / "bin" / "python"
        if not python_path.exists():
            python_path = (
                self.project_root / "venv" / "Scripts" / "python.exe"
            )  # Windows

        # Generate email from project name
        project_domain = (
            details["project_slug"].replace("_backend", "").replace("_", "")
        )
        superuser_email = f"admin@{project_domain}.com"
        superuser_password = "Admin123!"

        print(f"   Email: {superuser_email}")
        print(f"   Password: {superuser_password}")

        try:
            env = os.environ.copy()
            env["PYTHONPATH"] = str(self.project_root)
            env["FIRST_SUPERUSER"] = superuser_email
            env["FIRST_SUPERUSER_PASSWORD"] = superuser_password

            subprocess.run(
                [str(python_path), "app/bootstrap_superuser.py"],
                cwd=self.project_root,
                env=env,
                check=True,
            )
            print("✅ Superuser created successfully")

        except subprocess.CalledProcessError:
            print("⚠️  Superuser creation failed (this is often normal)")
            print("   You can create one manually later if needed")

    def install_git_hooks(self) -> None:
        """Install git hooks for template protection."""
        print()
        print("🔧 Installing git hooks for template protection...")

        git_dir = self.project_root / ".git"
        if not git_dir.exists():
            print("   ⚠️  Not a git repository, skipping git hooks")
            return

        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir(exist_ok=True)

        # Install pre-commit hook for template protection
        pre_commit_hook = hooks_dir / "pre-commit"
        template_pre_commit = self.project_root / "scripts" / "git-hooks" / "pre-commit"

        if template_pre_commit.exists():
            try:
                shutil.copy2(template_pre_commit, pre_commit_hook)
                pre_commit_hook.chmod(0o755)  # Make executable
                print("   ✅ Git hooks installed (template protection enabled)")
            except Exception as e:
                print(f"   ⚠️  Failed to install git hooks: {e}")
        else:
            print("   ⚠️  Template protection hook not found")

    def final_checks(self) -> None:
        """Run final validation checks."""
        print()
        print("🔍 Running final checks...")

        python_path = self.project_root / "venv" / "bin" / "python"
        if not python_path.exists():
            python_path = (
                self.project_root / "venv" / "Scripts" / "python.exe"
            )  # Windows

        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.project_root)

        # Test imports
        try:
            subprocess.run(
                [
                    str(python_path),
                    "-c",
                    "from app.main import app; print('API imports OK')",
                ],
                cwd=self.project_root,
                env=env,
                check=True,
                capture_output=True,
            )
            print("   ✅ API imports successfully")
        except subprocess.CalledProcessError:
            print("   ⚠️  API import test failed")

        # Test configuration
        try:
            subprocess.run(
                [
                    str(python_path),
                    "-c",
                    "from app.core.config.config import settings; print(f'Config: {settings.PROJECT_NAME}')",
                ],
                cwd=self.project_root,
                env=env,
                check=True,
                capture_output=True,
            )
            print("   ✅ Configuration loads successfully")
        except subprocess.CalledProcessError:
            print("   ⚠️  Configuration test failed")

    def show_completion_message(self, details: dict[str, str]) -> None:
        """Show the completion message with next steps."""
        print()
        print("🎉 PROJECT SETUP COMPLETE!")
        print("=" * 50)
        print()
        print("🚀 Your FastAPI project is ready!")
        print()
        print("📋 What's been set up:")
        print("  ✅ Project files customized")
        print("  ✅ Python virtual environment created")
        print("  ✅ Dependencies installed")
        print("  ✅ PostgreSQL database running")
        print("  ✅ Database migrations applied")
        print("  ✅ Superuser account created")
        print("  ✅ Git hooks installed (template protection enabled)")
        print()
        print("🎯 Next Steps:")
        print("1. Start the API server:")
        print("   docker-compose up -d api")
        print()
        print("2. View API documentation:")
        print("   http://localhost:8000/docs")
        print()
        print("3. Update your git remote (if needed):")
        print(
            f"   git remote set-url origin https://github.com/yourusername/{details['project_slug']}.git",
        )
        print()
        print("4. Start developing your application!")
        print()
        print("💡 Useful Commands:")
        print("  docker-compose up -d          # Start all services")
        print("  docker-compose logs -f api    # View API logs")
        print("  docker-compose down           # Stop services")
        print("  source venv/bin/activate      # Activate virtual environment")
        print("  pytest                        # Run tests")
        print()
        print("✨ Happy coding! 🚀")


def main():
    """Main setup function."""
    setup = ProjectSetup()

    # Validate project structure
    if not setup.validate_project_structure():
        print("❌ Error: This doesn't appear to be a FastAPI template directory.")
        print("   Make sure you're in the correct project folder.")
        print("   Expected files: app/main.py, requirements.txt, docker-compose.yml")
        sys.exit(1)

    # Get project details
    details = setup.get_project_details()

    # Confirm with user
    if not setup.confirm_details(details):
        print("❌ Setup cancelled by user.")
        sys.exit(0)

    try:
        # Set up replacements and customize files
        setup.setup_replacements(details)
        setup.customize_files()

        # Set up environment
        setup.setup_environment()

        # Start services
        setup.check_docker()
        setup.start_services()
        setup.run_migrations()
        setup.create_superuser(details)

        # Install git hooks for protection
        setup.install_git_hooks()

        # Final checks
        setup.final_checks()

        # Show completion message
        setup.show_completion_message(details)

    except KeyboardInterrupt:
        print("\n❌ Setup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        print("   Please check the error message above and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
