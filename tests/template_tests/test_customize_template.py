"""
Test the template customization script functionality.

Tests the template customization script to ensure it correctly transforms
template references into project-specific names.

These tests are template-specific and should be excluded when running
tests for user applications.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.customize_template import TemplateCustomizer


@pytest.mark.template_only
class TestTemplateCustomizer:
    """Test the TemplateCustomizer class functionality."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for testing."""
        temp_dir = tempfile.mkdtemp()
        project_dir = Path(temp_dir) / "fast-api-template"
        project_dir.mkdir()

        # Create some test files with template references
        test_files = {
            "README.md": "# Your Project Name\n\nA FastAPI application built with the [FastAPI Template](docs/TEMPLATE_README.md).",
            "app/core/config.py": 'PROJECT_NAME: str = "FastAPI Template"',
            "docker-compose.yml": "POSTGRES_DB: fastapi_template",
            "scripts/setup.sh": "echo 'Setting up FastAPI Template'",
            "docs/tutorials/getting-started.md": "Welcome to FastAPI Template",
        }

        for file_path, content in test_files.items():
            full_path = project_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

        yield project_dir

        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def customizer(self, temp_project_dir):
        """Create a TemplateCustomizer instance with test replacements."""
        customizer = TemplateCustomizer()
        customizer.project_root = temp_project_dir
        customizer.replacements = {
            "fast-api-template": "myawesomeproject_backend",
            "fastapi_template": "myawesomeproject_backend",
            "FastAPI Template": "My Awesome Project",
            "FastAPI Template with Authentication": "My Awesome Project API",
            "Your Name": "John Doe",
            "your.email@example.com": "john@example.com",
            "fast-api-template-postgres-1": "myawesomeproject_backend-postgres-1",
            "fast-api-template-postgres": "myawesomeproject_backend-postgres",
        }
        return customizer

    def test_get_files_to_process(self, customizer):
        """Test that get_files_to_process finds the correct files."""
        files = customizer.get_files_to_process()

        # Should find our test files
        file_paths = [f.name for f in files]
        assert "README.md" in file_paths
        assert "config.py" in file_paths
        assert "docker-compose.yml" in file_paths
        assert "setup.sh" in file_paths
        assert "getting-started.md" in file_paths

        # Should not include directories
        assert not any(f.is_dir() for f in files)

    def test_process_file(self, customizer):
        """Test that process_file correctly replaces template references."""
        test_file = customizer.project_root / "README.md"

        # Process the file
        result = customizer.process_file(test_file)

        # Should have made changes
        assert result is True

        # Check the content was updated
        content = test_file.read_text()
        assert "My Awesome Project" in content
        # The template link should still be preserved
        assert "[FastAPI Template](docs/TEMPLATE_README.md)" in content

    def test_process_file_no_changes(self, customizer):
        """Test that process_file returns False when no changes are made."""
        # Create a file with no template references
        test_file = customizer.project_root / "no_template.txt"
        test_file.write_text("This file has no template references.")

        # Process the file
        result = customizer.process_file(test_file)

        # Should not have made changes
        assert result is False

        # Content should be unchanged
        content = test_file.read_text()
        assert content == "This file has no template references."

    def test_process_file_handles_errors(self, customizer):
        """Test that process_file handles errors gracefully."""
        # Create a file that can't be read
        test_file = customizer.project_root / "binary_file.bin"
        test_file.write_bytes(b"\x00\x01\x02\x03")

        # Process should not crash
        result = customizer.process_file(test_file)
        assert result is False

    def test_create_customization_log(self, customizer):
        """Test that create_customization_log creates the expected log file."""
        customizer.create_customization_log()

        log_file = customizer.project_root / "docs" / "TEMPLATE_CUSTOMIZATION.md"
        assert log_file.exists()

        content = log_file.read_text()
        assert "Template Customization Log" in content
        assert "My Awesome Project" in content
        assert "myawesomeproject_backend" in content
        assert "John Doe" in content
        assert "john@example.com" in content

    @patch("subprocess.run")
    def test_update_git_remote_template_repo(self, mock_run, customizer):
        """Test git remote update when pointing to template repository."""
        # Mock git remote pointing to template repo
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "https://github.com/user/fast-api-template.git"

        # This should not raise an exception
        customizer.update_git_remote()

        # Should have called git remote get-url
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_update_git_remote_custom_repo(self, mock_run, customizer):
        """Test git remote update when pointing to custom repository."""
        # Mock git remote pointing to custom repo
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = (
            "https://github.com/user/myawesomeproject_backend.git"
        )

        # This should not raise an exception
        customizer.update_git_remote()

        # Should have called git remote get-url
        mock_run.assert_called_once()

    def test_update_git_remote_no_git(self, customizer):
        """Test git remote update when git is not available."""
        # Remove .git directory to simulate no git repo
        git_dir = customizer.project_root / ".git"
        if git_dir.exists():
            shutil.rmtree(git_dir)

        # This should not raise an exception
        customizer.update_git_remote()

    def test_rename_project_directory(self, customizer):
        """Test that rename_project_directory provides instructions and creates workspace."""
        current_dir = customizer.project_root.name
        new_name = customizer.replacements.get("fast-api-template", "test_project")

        # Test that the method provides instructions without actually renaming
        if current_dir != new_name:
            # Should not raise any exceptions
            customizer.rename_project_directory()

            # Directory should still exist with original name
            assert customizer.project_root.exists()
            assert customizer.project_root.name == current_dir

            # VS Code workspace file creation is now disabled, so just check directory exists
            assert customizer.project_root.exists()

    def test_rename_project_directory_same_name(self, customizer):
        """Test that rename_project_directory handles same directory name."""
        current_dir = customizer.project_root.name
        # Set replacement to same name
        customizer.replacements["fast-api-template"] = current_dir

        # Should not raise any exceptions
        customizer.rename_project_directory()

        # Directory should still exist with same name (no rename needed)
        assert customizer.project_root.exists()
        assert customizer.project_root.name == current_dir


@pytest.mark.template_only
class TestTemplateCustomizerIntegration:
    """Integration tests for the template customization process."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a more realistic temporary project directory."""
        temp_dir = tempfile.mkdtemp()
        project_dir = Path(temp_dir) / "fast-api-template"
        project_dir.mkdir()

        # Create a more realistic project structure
        test_files = {
            "README.md": """# FastAPI Template

A comprehensive, production-ready FastAPI template with authentication, admin panel, API keys, audit logging, and more.

## Quick Start

```bash
cd fast-api-template
./scripts/setup_comprehensive.sh
```
""",
            "app/core/config.py": '''"""Configuration settings for the FastAPI Template application."""

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Template"
    DESCRIPTION: str = "FastAPI Template with Authentication"
    FROM_NAME: str = "FastAPI Template"

    class Config:
        env_file = ".env"
''',
            "docker-compose.yml": """version: '3.8'

services:
  postgres:
    environment:
      POSTGRES_DB: fastapi_template
    ports:
      - "5432:5432"
""",
            "scripts/setup.sh": """#!/bin/bash
echo "🚀 Setting up FastAPI Template Development Environment"
""",
            "docs/tutorials/getting-started.md": """# Getting Started with FastAPI Template

Welcome! This guide will walk you through creating a new application based on this FastAPI template.
""",
            "app/main.py": '''"""Main FastAPI application."""

from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
)

@app.get("/")
def read_root():
    return {"message": "Welcome to FastAPI Template"}
''',
        }

        for file_path, content in test_files.items():
            full_path = project_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

        yield project_dir

        # Cleanup
        shutil.rmtree(temp_dir)

    @patch("builtins.input")
    @patch("builtins.print")
    def test_full_customization_process(self, mock_print, mock_input, temp_project_dir):
        """Test the complete customization process with user input."""
        # Mock user input
        mock_input.side_effect = [
            "My Awesome Project",  # Project name
            "myawesomeproject_backend",  # Project slug
            "myawesomeproject_backend",  # Database name
            "myawesomeproject_backend",  # Docker prefix
            "Backend API for My Awesome Project",  # Description
            "John Doe",  # Author
            "john@example.com",  # Email
            "y",  # Confirm
        ]

        # Create customizer and run
        customizer = TemplateCustomizer()
        customizer.project_root = temp_project_dir

        # Mock the file processing to avoid actual file operations
        with patch.object(customizer, "get_files_to_process") as mock_get_files:
            mock_get_files.return_value = [
                temp_project_dir / "README.md",
                temp_project_dir / "app/core/config.py",
                temp_project_dir / "docker-compose.yml",
                temp_project_dir / "scripts/setup.sh",
                temp_project_dir / "docs/tutorials/getting-started.md",
                temp_project_dir / "app/main.py",
            ]

            # Run the customization
            customizer.run()

        # Verify the replacements were set correctly
        assert customizer.replacements["FastAPI Template"] == "My Awesome Project"
        assert (
            customizer.replacements["fast-api-template"] == "myawesomeproject_backend"
        )
        assert customizer.replacements["fastapi_template"] == "myawesomeproject_backend"
        assert customizer.replacements["Your Name"] == "John Doe"
        assert customizer.replacements["your.email@example.com"] == "john@example.com"

    def test_customization_creates_log_file(self, temp_project_dir):
        """Test that customization creates the expected log file."""
        customizer = TemplateCustomizer()
        customizer.project_root = temp_project_dir
        customizer.replacements = {
            "fast-api-template": "myawesomeproject_backend",
            "fastapi_template": "myawesomeproject_backend",
            "FastAPI Template": "My Awesome Project",
            "FastAPI Template with Authentication": "Backend API for My Awesome Project",
            "Your Name": "John Doe",
            "your.email@example.com": "john@example.com",
            "fast-api-template-postgres-1": "myawesomeproject_backend-postgres-1",
            "fast-api-template-postgres": "myawesomeproject_backend-postgres",
        }

        # Create the log file
        customizer.create_customization_log()

        # Check the log file exists and has correct content
        log_file = temp_project_dir / "docs" / "TEMPLATE_CUSTOMIZATION.md"
        assert log_file.exists()

        content = log_file.read_text()
        assert "Template Customization Log" in content
        assert "My Awesome Project" in content
        assert "myawesomeproject_backend" in content
        assert "John Doe" in content
        assert "john@example.com" in content
        assert "Backend API for My Awesome Project" in content
