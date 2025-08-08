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

⚠️  IMPORTANT: This script requires interactive human input.
    It cannot be automated or run non-interactively.

Designed for GitHub "Use this template" workflow:
1. Click "Use this template" on GitHub
2. Clone your new repository
3. Run this script directly in your terminal
"""

import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


class ProjectSetup:
    def __init__(self):
        self.project_root = Path.cwd()
        self.current_dir_name = self.project_root.name
        self.replacements: dict[str, str] = {}
        self.port_overrides: dict[str, int] = {}

    def ensure_interactive(self) -> None:
        """Require interactive TTY - no overrides allowed.

        This setup script requires human input for project customization.
        It cannot be run non-interactively or automated.
        """
        # Check for TTY
        if not sys.stdin.isatty():
            print("❌ This script requires interactive mode.")
            print("   You must run this script directly in a terminal.")
            print("   Automated/non-interactive execution is not supported.")
            print()
            print("   This ensures you can customize your project details personally.")
            sys.exit(1)

        # Additional check for process tree to detect automation
        try:
            import psutil

            current_proc = psutil.Process()
            parent_proc = current_proc.parent()

            # Check if parent process suggests automation
            if parent_proc and parent_proc.name() in [
                "python",
                "python3",
                "node",
                "bash",
                "sh",
                "zsh",
            ]:
                grandparent = parent_proc.parent()
                if grandparent and grandparent.name() in [
                    "python",
                    "python3",
                    "node",
                    "Code",
                    "cursor",
                ]:
                    print("❌ Automated execution detected via process tree.")
                    print("   This script must be run directly by a human user.")
                    print("   Please run it manually in your terminal.")
                    sys.exit(1)
        except ImportError:
            # psutil not available, continue with basic checks
            pass
        except Exception:
            # Any error in process checking, continue
            pass

    # -------------------------------
    # Port helpers
    # -------------------------------
    def _is_port_in_use(self, port: int, host: str = "127.0.0.1") -> bool:
        """Return True if the TCP port is already in use on the host."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.3)
            result = sock.connect_ex((host, port))
            return result == 0

    def _find_available_port(
        self,
        start_port: int,
        host: str = "127.0.0.1",
        max_tries: int = 50,
    ) -> int:
        """Find the next available TCP port starting at start_port."""
        port = start_port
        tries = 0
        while tries < max_tries and self._is_port_in_use(port, host=host):
            port += 1
            tries += 1
        return port

    def _read_env_file(self) -> dict[str, str]:
        """Read .env file into a dict (best-effort)."""
        env_path = self.project_root / ".env"
        values: dict[str, str] = {}
        if not env_path.exists():
            return values
        try:
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    values[key.strip()] = val.strip()
        except Exception:
            # Ignore parse errors and return whatever we got
            pass
        return values

    def _write_env_updates(self, updates: dict[str, str]) -> None:
        """Update or append keys in .env file with provided values."""
        env_path = self.project_root / ".env"
        existing_lines: list[str] = []
        if env_path.exists():
            try:
                existing_lines = env_path.read_text(encoding="utf-8").splitlines()
            except Exception:
                existing_lines = []

        # Map of existing keys to their current line index
        key_to_index: dict[str, int] = {}
        for idx, line in enumerate(existing_lines):
            if not line or line.lstrip().startswith("#"):
                continue
            if "=" in line:
                key, _ = line.split("=", 1)
                key_to_index[key.strip()] = idx

        for key, value in updates.items():
            if key in key_to_index:
                existing_lines[key_to_index[key]] = f"{key}={value}"
            else:
                existing_lines.append(f"{key}={value}")

        # Ensure newline at end
        content = "\n".join(existing_lines).rstrip() + "\n"
        env_path.write_text(content, encoding="utf-8")

    def resolve_service_ports(self) -> None:
        """Detect host port conflicts and pick alternative ports, updating .env and environment.

        Services and defaults considered:
        - POSTGRES_PORT (5432)
        - PGBOUNCER_PORT (5433)
        - REDIS_PORT (6379)
        - API_PORT (8000)
        - FLOWER_PORT (5555)
        - GLITCHTIP_PORT (8001)
        """
        print()
        print("🔎 Checking for port conflicts...")

        env_values = self._read_env_file()

        desired_ports: dict[str, int] = {
            "POSTGRES_PORT": int(
                env_values.get("POSTGRES_PORT")
                or os.environ.get("POSTGRES_PORT", 5432),
            ),
            "PGBOUNCER_PORT": int(
                env_values.get("PGBOUNCER_PORT")
                or os.environ.get("PGBOUNCER_PORT", 5433),
            ),
            "REDIS_PORT": int(
                env_values.get("REDIS_PORT") or os.environ.get("REDIS_PORT", 6379),
            ),
            "API_PORT": int(
                env_values.get("API_PORT") or os.environ.get("API_PORT", 8000),
            ),
            "FLOWER_PORT": int(
                env_values.get("FLOWER_PORT") or os.environ.get("FLOWER_PORT", 5555),
            ),
            "GLITCHTIP_PORT": int(
                env_values.get("GLITCHTIP_PORT")
                or os.environ.get("GLITCHTIP_PORT", 8001),
            ),
        }

        updates: dict[str, str] = {}
        any_conflicts = False

        for key, desired in desired_ports.items():
            if self._is_port_in_use(desired):
                any_conflicts = True
                suggested = self._find_available_port(desired + 1)
                # Allow user to accept or provide custom port
                try:
                    response = self._safe_input(
                        f"   ⚠️  Port {desired} for {key} is in use. Use {suggested} instead? [Y/n/custom]: ",
                    ).strip()
                    if response.lower() in ("", "y", "yes"):  # accept suggested
                        new_port = suggested
                    elif response.lower() in ("n", "no"):
                        # Keep original (may fail later)
                        new_port = desired
                    else:
                        try:
                            new_port = int(response)
                        except ValueError:
                            print(
                                f"   ⚠️  Invalid custom port '{response}'. Using suggested {suggested}.",
                            )
                            new_port = suggested
                except Exception:
                    new_port = suggested

                if new_port != desired:
                    print(f"   🔁 Setting {key} to {new_port} (was {desired})")
                    updates[key] = str(new_port)
                    self.port_overrides[key] = new_port
            else:
                # Ensure the value is present in .env so compose uses it
                updates[key] = str(desired)

        if updates:
            self._write_env_updates(updates)
            # Also set in current env for subprocesses
            for k, v in updates.items():
                os.environ[k] = v

        if any_conflicts:
            print("✅ Port conflicts resolved via .env updates")
        else:
            print("✅ No port conflicts detected")

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

    def get_python_executable(self) -> str:
        """Find and validate the correct Python executable (3.11+)."""
        # List of Python executables to try in order of preference
        python_candidates = [
            "python3.11",
            "python3.12",
            "python3.13",
            "python3.10",  # Minimum fallback
            "python3",
            "python",
        ]

        for python_exe in python_candidates:
            try:
                # Check if the executable exists and get version
                result = subprocess.run(
                    [python_exe, "--version"],
                    capture_output=True,
                    text=True,
                    check=True,
                )

                # Parse version (output like "Python 3.11.0")
                version_str = result.stdout.strip()
                if "Python " in version_str:
                    version_part = version_str.split("Python ")[1]
                    major, minor = map(int, version_part.split(".")[:2])

                    # Check if version is 3.10+ (minimum requirement)
                    if major == 3 and minor >= 10:
                        print(f"   Found Python {major}.{minor} at {python_exe}")
                        if minor < 11:
                            print(
                                f"   ⚠️  Warning: Python 3.11+ recommended, found {major}.{minor}",
                            )
                        return python_exe

            except (
                subprocess.CalledProcessError,
                FileNotFoundError,
                ValueError,
                IndexError,
            ):
                continue

        # No suitable Python found
        print("❌ Error: No suitable Python version found!")
        print("   This project requires Python 3.10+ (3.11+ recommended)")
        print("   Please install Python 3.11+ and ensure it's in your PATH")
        print(
            "   Try: brew install python@3.11 (macOS) or apt install python3.11 (Ubuntu)",
        )
        sys.exit(1)

    def _safe_input(self, prompt: str) -> str:
        """Get input with additional automation detection."""
        try:
            # Record timing to detect rapid automated responses
            start_time = time.time()

            # Add a small delay to detect rapid automated input
            time.sleep(0.1)
            response = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Input interrupted or piped. This script requires manual input.")
            print("   Please run this script directly without automation or piping.")
            sys.exit(1)
        else:
            # Check if response came suspiciously fast (likely automated)
            response_time = time.time() - start_time
            if response_time < 0.5:  # Less than 500ms suggests automation
                print("\n❌ Response too fast - automation detected.")
                print(
                    "   Please take time to read and answer each question thoughtfully.",
                )
                print(
                    "   This script requires human consideration for project customization.",
                )
                sys.exit(1)

            return response

    def get_project_details(self) -> dict[str, str]:
        """Get project details from user input."""
        print("🚀 FastAPI Project Setup")
        print("=" * 50)
        print()
        print("Setting up your FastAPI project...")
        print()
        print("⚠️  This setup requires your personal input for project customization.")
        print("   Please answer each question thoughtfully.")
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

        user_name = self._safe_input(f"Project name [{name_from_slug}]: ").strip()
        details["project_name"] = user_name if user_name else name_from_slug

        # Get other details
        details["author_name"] = (
            self._safe_input("Author name: ").strip() or "Your Name"
        )
        details["author_email"] = (
            self._safe_input("Author email: ").strip() or "your.email@example.com"
        )

        # Generate database name from slug
        db_name = details["project_slug"].replace("-", "_").lower()
        user_db = self._safe_input(f"Database name [{db_name}]: ").strip()
        details["database_name"] = user_db if user_db else db_name

        # Generate description
        default_desc = f"A FastAPI backend for {details['project_name']}"
        user_desc = self._safe_input(f"Project description [{default_desc}]: ").strip()
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
        confirm = self._safe_input("Proceed with setup? (y/N): ").strip().lower()
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

    def _update_env_file_with_replacements(self, env_file: Path) -> None:
        """Update .env file with custom replacements."""
        if not env_file.exists():
            return

        # Read current .env content
        content = env_file.read_text()

        # Update database name in environment variables
        if "fastapi_template" in self.replacements:
            db_name = self.replacements["fastapi_template"]

            # Replace POSTGRES_DB value
            content = re.sub(r"POSTGRES_DB=.*", f"POSTGRES_DB={db_name}", content)

            # Replace DATABASE_URL value
            content = re.sub(
                r"DATABASE_URL=postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/([^\s]+)",
                f"DATABASE_URL=postgresql://\\1:\\2@\\3:\\4/{db_name}",
                content,
            )

            # Write updated content back
            env_file.write_text(content)

    def _ensure_database_exists(self) -> bool:
        """Ensure the target database exists in PostgreSQL."""
        # Get database name from replacements
        db_name = "fastapi_template"
        if hasattr(self, "replacements") and "fastapi_template" in self.replacements:
            db_name = self.replacements["fastapi_template"]

        print(f"   Checking if database '{db_name}' exists...")

        try:
            # Check if database exists
            result = subprocess.run(
                [
                    "docker-compose",
                    "exec",
                    "-T",
                    "postgres",
                    "psql",
                    "-U",
                    "postgres",
                    "-lqt",
                ],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                print(f"   ❌ Could not check databases: {result.stderr}")
                return False

            # Parse database list
            databases = []
            for line in result.stdout.split("\n"):
                if "|" in line:
                    db_parts = line.split("|")
                    if len(db_parts) > 0:
                        databases.append(db_parts[0].strip())

            if db_name in databases:
                print(f"   ✅ Database '{db_name}' exists")
                return True

            # Database doesn't exist, create it
            print(f"   Creating database '{db_name}'...")
            create_result = subprocess.run(
                [
                    "docker-compose",
                    "exec",
                    "-T",
                    "postgres",
                    "createdb",
                    "-U",
                    "postgres",
                    db_name,
                ],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False,
            )

            # ruff: noqa: RET505
            if create_result.returncode == 0:
                print(f"   ✅ Database '{db_name}' created successfully")
                return True
            else:
                print(f"   ❌ Failed to create database: {create_result.stderr}")
                return False

        except Exception as e:
            print(f"   ❌ Error checking/creating database: {e}")
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

            # Update .env file with custom database name
            if hasattr(self, "replacements"):
                self._update_env_file_with_replacements(env_file)

            print("   ✅ .env file created")

        # Create virtual environment with proper Python version
        venv_dir = self.project_root / "venv"
        if not venv_dir.exists():
            print("   Creating Python virtual environment...")
            python_exe = self.get_python_executable()
            subprocess.run(
                [python_exe, "-m", "venv", "venv"],
                cwd=self.project_root,
                check=True,
            )
            print(f"   ✅ Virtual environment created with {python_exe}")

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

    def start_services(self) -> bool:
        """Start Docker services (Postgres first, API after migrations)."""
        print()
        print("🗄️  Starting database service...")

        try:
            # Start only PostgreSQL first
            subprocess.run(
                ["docker-compose", "up", "-d", "postgres"],
                cwd=self.project_root,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"❌ Error starting PostgreSQL: {e}")
            return False
        else:
            print("✅ PostgreSQL container started")

            # Wait for PostgreSQL
            print("⏳ Waiting for PostgreSQL to be ready...")
            self.wait_for_postgres()
            return True

    def start_api_service(self) -> bool:
        """Start the API service after migrations are complete."""
        print()
        print("🚀 Starting API service...")

        try:
            subprocess.run(
                ["docker-compose", "up", "-d", "api"],
                cwd=self.project_root,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"❌ Error starting API: {e}")
            print("   Continuing with setup, but API may not be available...")
            return False
        else:
            print("✅ API container started")

            # Wait for API to respond on health endpoint
            print("⏳ Waiting for API to be ready...")
            time.sleep(5)  # Give API container time to fully initialize
            self.wait_for_api()
            return True

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

    def wait_for_api(self) -> None:
        """Wait for the API health endpoint to respond."""
        api_port_str = os.environ.get("API_PORT", "8000")
        try:
            api_port = int(api_port_str)
        except ValueError:
            api_port = 8000

        url = f"http://127.0.0.1:{api_port}/system/health"
        last_error = None

        for i in range(45):  # ~90 seconds max
            try:
                with urllib.request.urlopen(url, timeout=2) as resp:
                    status = resp.getcode()
                    if status == 200:
                        print(f"✅ API is responding on http://127.0.0.1:{api_port}")
                        return
                    else:
                        last_error = f"HTTP {status}"
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
                last_error = e
                if i < 3:  # Log first few connection attempts for debugging
                    error_msg = str(e)
                    if (
                        "Connection reset by peer" in error_msg
                        or "Connection refused" in error_msg
                    ):
                        print(f"   API still starting up... (attempt {i+1})")
                    else:
                        print(f"   Connection attempt failed: {type(e).__name__}: {e}")

            if i == 44:
                print("❌ API failed to become ready. Checking container status...")
                self._diagnose_api_failure(last_error)
                return

            if i % 10 == 0 and i > 0:  # Every 20 seconds
                print(f"   Still waiting for API... ({i+1}/45)")
            time.sleep(2)

    def _diagnose_api_failure(self, last_error) -> None:
        """Diagnose why the API container failed to start."""
        print(f"   Last connection error: {last_error}")
        print("   Running diagnostics...")

        try:
            # Check if API container is running
            result = subprocess.run(
                ["docker-compose", "ps", "api"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            print(f"   Container status:\n{result.stdout}")

            # Get API container logs
            result = subprocess.run(
                ["docker-compose", "logs", "--tail=20", "api"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            if result.stdout:
                print(f"   Recent API logs:\n{result.stdout}")
            if result.stderr:
                print(f"   API error logs:\n{result.stderr}")

        except subprocess.CalledProcessError as e:
            print(f"   Could not get diagnostics: {e}")

        print()
        print("🔧 Common fixes:")
        print("   1. Check the API logs: docker-compose logs api")
        print("   2. Restart containers: docker-compose restart")
        print("   3. Rebuild API: docker-compose build api")
        print("   4. Check database connection in .env file")

    def run_migrations(self) -> bool:
        """Run database migrations."""
        print()
        print("🔄 Running database migrations...")

        # Ensure database exists before running migrations
        if not self._ensure_database_exists():
            return False

        python_path = self.project_root / "venv" / "bin" / "python"
        if not python_path.exists():
            python_path = (
                self.project_root / "venv" / "Scripts" / "python.exe"
            )  # Windows

        # Create alembic.ini if it doesn't exist
        alembic_ini = self.project_root / "alembic.ini"
        if not alembic_ini.exists():
            print("   Creating alembic.ini file...")
            self.create_alembic_ini()

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
        except subprocess.CalledProcessError as e:
            print(f"❌ Error running migrations: {e}")
            return False
        else:
            if result.returncode == 0:
                print("✅ Database migrations completed successfully")
                return True
            print("❌ Database migrations failed!")
            print("   Error output:")
            if result.stderr:
                print(f"   {result.stderr}")
            if result.stdout:
                print(f"   {result.stdout}")
            print("   Please check your database configuration and Alembic setup")
            return False

    def create_alembic_ini(self) -> None:
        """Create alembic.ini file if it doesn't exist."""
        alembic_ini = self.project_root / "alembic.ini"

        # Get database name from replacements or use default
        db_name = "fastapi_template"
        if hasattr(self, "replacements") and "fastapi_template" in self.replacements:
            db_name = self.replacements["fastapi_template"]

        content = f"""# A generic, single database configuration.

[alembic]
# path to migration scripts
script_location = alembic

# template used to generate migration file names; The default value is %%(rev)s_%%(slug)s
# Uncomment the line below if you want the files to be prepended with date and time
# file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s

# sys.path path, will be prepended to sys.path if present.
# defaults to the current working directory.
prepend_sys_path = .

# timezone to use when rendering the date within the migration file
# as well as the filename.
# If specified, requires the python-dateutil library that can be
# installed by adding `alembic[tz]` to the pip requirements
# string value is passed to dateutil.tz.gettz()
# leave blank for localtime
# timezone =

# max length of characters to apply to the
# "slug" field
# truncate_slug_length = 40

# set to 'true' to run the environment during
# the 'revision' command, regardless of autogenerate
# revision_environment = false

# set to 'true' to allow .pyc and .pyo files without
# a source .py file to be detected as revisions in the
# versions/ directory
# sourceless = false

# version number format
version_num_format = %%04d

# version path separator; As mentioned above, this is the character used to split
# version_locations. The default within new alembic.ini files is "os", which uses
# os.pathsep. If this key is omitted entirely, it falls back to the legacy
# behavior of splitting on spaces and/or commas.
# Valid values for version_path_separator are:
#
# version_path_separator = :
# version_path_separator = ;
# version_path_separator = space
version_path_separator = os

# the output encoding used when revision files
# are written from script.py.mako
# output_encoding = utf-8

sqlalchemy.url = postgresql://postgres:dev_password_123@localhost:5432/{db_name}


[post_write_hooks]
# post_write_hooks defines scripts or Python functions that are run
# on newly generated revision scripts.  See the documentation for further
# detail and examples

# format using "black" - use the console_scripts runner, against the "black" entrypoint
# hooks = black
# black.type = console_scripts
# black.entrypoint = black
# black.options = -l 79 REVISION_SCRIPT_FILENAME

# lint with attempts to fix using "ruff" - use the exec runner, execute a binary
# hooks = ruff
# ruff.type = exec
# ruff.executable = %(here)s/.venv/bin/ruff
# ruff.options = --fix REVISION_SCRIPT_FILENAME

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""

        with alembic_ini.open("w", encoding="utf-8") as f:
            f.write(content)
        print("   ✅ alembic.ini file created")

    def create_superuser(self, details: dict[str, str]) -> bool:
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

            result = subprocess.run(
                [str(python_path), "app/bootstrap_superuser.py"],
                cwd=self.project_root,
                env=env,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"❌ Error creating superuser: {e}")
            return False
        else:
            if result.returncode == 0:
                print("✅ Superuser created successfully")
                # Check for harmless bcrypt warning
                if "bcrypt" in result.stderr and "__about__" in result.stderr:
                    print(
                        "   ℹ️  Note: bcrypt version warning is harmless and can be ignored",
                    )
                # Verify the superuser was created and set is_verified=True
                self.verify_superuser(superuser_email)
                return True
            print("❌ Superuser creation failed!")
            print("   Error output:")
            if result.stderr:
                print(f"   {result.stderr}")
            if result.stdout:
                print(f"   {result.stdout}")
            print("   This often happens if the database tables don't exist")
            print("   Make sure migrations completed successfully first")
            return False

    def verify_superuser(self, email: str) -> None:
        """Verify the superuser account by setting is_verified=True."""
        print("   Verifying superuser account...")

        python_path = self.project_root / "venv" / "bin" / "python"
        if not python_path.exists():
            python_path = (
                self.project_root / "venv" / "Scripts" / "python.exe"
            )  # Windows

        # Create a temporary script to verify the user
        verify_script = self.project_root / "verify_superuser_temp.py"
        script_content = f"""
import asyncio
from sqlalchemy import select, update
from app.database.database import engine
from app.models.auth.user import User

async def verify_user():
    try:
        async with engine.begin() as conn:
            # Update user to be verified
            await conn.execute(
                update(User).where(User.email == "{email}").values(is_verified=True)
            )
            print("✅ Superuser verified successfully")
    except Exception as e:
        print(f"⚠️  Could not verify superuser: {{e}}")

if __name__ == "__main__":
    asyncio.run(verify_user())
"""

        try:
            with verify_script.open("w", encoding="utf-8") as f:
                f.write(script_content)

            env = os.environ.copy()
            env["PYTHONPATH"] = str(self.project_root)

            subprocess.run(
                [str(python_path), str(verify_script)],
                cwd=self.project_root,
                env=env,
                check=True,
                capture_output=True,
            )

        except subprocess.CalledProcessError:
            print("   ⚠️  Could not verify superuser (this is often normal)")
        finally:
            # Clean up temporary script
            if verify_script.exists():
                verify_script.unlink()

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

    def final_checks(self) -> bool:
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

        checks_passed = 0
        total_checks = 3

        # Test Python version compatibility
        try:
            result = subprocess.run(
                [str(python_path), "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            version_str = result.stdout.strip()
            if "Python " in version_str:
                version_part = version_str.split("Python ")[1]
                major, minor = map(int, version_part.split(".")[:2])
                if major == 3 and minor >= 10:
                    print(
                        f"   ✅ Python version {major}.{minor} compatibility confirmed",
                    )
                    checks_passed += 1
                else:
                    print(
                        f"   ❌ Python version {major}.{minor} is too old (need 3.10+)",
                    )
            else:
                print("   ❌ Could not determine Python version")
        except (subprocess.CalledProcessError, ValueError, IndexError):
            print("   ❌ Python version check failed")

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
            checks_passed += 1
        except subprocess.CalledProcessError:
            print("   ❌ API import test failed")
            print(
                "   This usually means the virtual environment has the wrong Python version",
            )

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
            checks_passed += 1
        except subprocess.CalledProcessError:
            print("   ❌ Configuration test failed")
            print(
                "   This usually means the virtual environment has the wrong Python version",
            )

        success = checks_passed == total_checks
        if success:
            print(f"✅ All {total_checks} validation checks passed!")
        else:
            print(f"⚠️  Only {checks_passed}/{total_checks} validation checks passed")

        return success

    def show_completion_message(
        self,
        details: dict[str, str],
        services_success: bool,
        migrations_success: bool,
        superuser_success: bool,
        validation_success: bool,
    ) -> None:
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
        print(
            f"  {'✅' if services_success else '❌'} Docker services {'started successfully' if services_success else 'started with issues'}",
        )
        print(
            f"  {'✅' if migrations_success else '❌'} Database migrations {'applied' if migrations_success else 'failed'}",
        )
        print(
            f"  {'✅' if superuser_success else '❌'} Superuser account {'created' if superuser_success else 'failed'}",
        )
        print("  ✅ Git hooks installed (template protection enabled)")
        print(
            f"  {'✅' if validation_success else '❌'} Final validation checks {'passed' if validation_success else 'failed'}",
        )

        if (
            not services_success
            or not migrations_success
            or not superuser_success
            or not validation_success
        ):
            print()
            print("⚠️  Some setup steps failed. You may need to:")
            if not services_success:
                print("   - Check API container logs: docker-compose logs api")
                print("   - Restart services: docker-compose restart")
                print("   - Rebuild API container: docker-compose build api")
            if not migrations_success:
                print("   - Check your database configuration")
                print("   - Run migrations manually: python -m alembic upgrade head")
            if not superuser_success:
                print("   - Create a superuser manually after fixing migrations")
                print("   - Run: python app/bootstrap_superuser.py")
            if not validation_success:
                print("   - Recreate virtual environment with Python 3.11+")
                print("   - Check that all dependencies installed correctly")

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

    # Require interactive terminal to prevent automation from answering prompts
    setup.ensure_interactive()

    # Clear warning about automation
    print("🚨 ANTI-AUTOMATION NOTICE:")
    print("   This script detects and blocks automated execution.")
    print("   You must personally answer each question for project customization.")
    print("   Rapid responses or automation tools will be rejected.")
    print()
    time.sleep(1)  # Give user time to read

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

        # Start services in the correct order
        setup.check_docker()
        # Detect and resolve host port conflicts before starting containers
        setup.resolve_service_ports()

        # 1. Start PostgreSQL first
        postgres_success = setup.start_services()

        # 2. Run migrations (creates database)
        migrations_success = setup.run_migrations() if postgres_success else False

        # 3. Create superuser
        superuser_success = (
            setup.create_superuser(details) if migrations_success else False
        )

        # 4. Start API service after database is ready
        api_success = setup.start_api_service() if migrations_success else False
        services_success = postgres_success and api_success

        # Install git hooks for protection
        setup.install_git_hooks()

        # Final checks
        validation_success = setup.final_checks()

        # Show completion message
        setup.show_completion_message(
            details,
            services_success,
            migrations_success,
            superuser_success,
            validation_success,
        )

    except KeyboardInterrupt:
        print("\n❌ Setup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        print("   Please check the error message above and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
