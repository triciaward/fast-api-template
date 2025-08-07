# mypy: disable-error-code="import-not-found"
"""
Test the simplified template customization script.

This test verifies that the customization script:
1. Checks directory name and warns if still in template directory
2. Processes files immediately after user input
3. Completes customization in one run
"""

import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add the scripts directory to the path BEFORE importing
scripts_path = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_path))

# Now import the customize_template module
try:
    # type: ignore[import-not-found]
    from customize_template import TemplateCustomizer
except ImportError:
    # Fallback: try to import from scripts directory directly
    scripts_abs_path = Path(__file__).parent.parent.parent / "scripts"
    if str(scripts_abs_path) not in sys.path:
        sys.path.insert(0, str(scripts_abs_path))
    # type: ignore[import-not-found]
    from customize_template import TemplateCustomizer


class TestTemplateCustomization:
    """Test the simplified template customization script."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir) / "fast-api-template"
        self.project_root.mkdir()

        # Create minimal project structure
        (self.project_root / "scripts").mkdir()
        (self.project_root / "app").mkdir()
        (self.project_root / "docs").mkdir()

        # Create test files
        test_files = [
            "README.md",
            "docker-compose.yml",
            "requirements.txt",
            "scripts/customize_template.py",
            "app/main.py",
            ".env.example",
        ]

        for file_path in test_files:
            full_path = self.project_root / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with full_path.open("w") as f:
                f.write(f"# Test file: {file_path}\n")
                f.write("fast-api-template\n")
                f.write("fastapi_template\n")
                f.write("FastAPI Template\n")

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("builtins.input")
    def test_directory_check_warns_on_template_name(self, mock_input):
        """Test that the script warns when still in template directory."""
        # Mock user to continue anyway
        mock_input.return_value = "y"

        # Create customizer with template directory name
        with patch.object(TemplateCustomizer, "__init__", lambda _self: None):
            customizer = TemplateCustomizer()
            customizer.project_root = self.project_root

            with patch("builtins.print") as mock_print:
                # The script should exit when it detects template directory
                with pytest.raises(SystemExit) as exc_info:
                    customizer.verify_directory_name()

                # Verify exit code
                assert exc_info.value.code == 1

                # Verify error message was displayed
                mock_print.assert_any_call(
                    "❌ Error: You're still in the 'fast-api-template' directory!",
                )

    @patch("builtins.input")
    def test_directory_check_exits_on_no_continue(self, mock_input):
        """Test that the script exits when user doesn't want to continue."""
        # Mock user to not continue
        mock_input.return_value = "n"

        # Create customizer with template directory name
        with patch.object(TemplateCustomizer, "__init__", lambda _self: None):
            customizer = TemplateCustomizer()
            customizer.project_root = self.project_root

            with patch("sys.exit") as mock_exit, patch("builtins.print") as mock_print:
                customizer.verify_directory_name()

                # Verify exit was called
                mock_exit.assert_called_once_with(1)
                mock_print.assert_any_call(
                    "❌ Error: You're still in the 'fast-api-template' directory!",
                )

    def test_directory_check_approves_custom_name(self):
        """Test that the script approves custom directory names."""
        # Create customizer with custom directory name
        custom_project_root = Path(self.temp_dir) / "myawesomeproject_backend"
        custom_project_root.mkdir()

        with patch.object(TemplateCustomizer, "__init__", lambda _self: None):
            customizer = TemplateCustomizer()
            customizer.project_root = custom_project_root

            with patch("builtins.print") as mock_print:
                customizer.verify_directory_name()

                # Verify approval message
                mock_print.assert_any_call(
                    "✅ Directory name looks good: myawesomeproject_backend",
                )

    @patch("builtins.input")
    def test_complete_customization_flow(self, mock_input):
        """Test the complete customization flow."""
        # Mock user input
        mock_input.side_effect = [
            "Test Project",  # Project name
            "test_project_backend",  # Project slug
            "test_project_backend",  # Database name
            "test_project_backend",  # Docker prefix
            "Test description",  # Description
            "Test Author",  # Author
            "test@example.com",  # Email
            "y",  # Confirm customization
        ]

        # Create customizer with custom directory name
        custom_project_root = Path(self.temp_dir) / "test_project_backend"
        custom_project_root.mkdir()

        # Copy test files to custom directory
        for file_path in [
            "README.md",
            "docker-compose.yml",
            "requirements.txt",
            ".env.example",
        ]:
            src = self.project_root / file_path
            dst = custom_project_root / file_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

        with patch.object(TemplateCustomizer, "__init__", lambda _self: None):
            customizer = TemplateCustomizer()
            customizer.project_root = custom_project_root
            customizer.replacements = {
                "fast-api-template": "test_project_backend",
                "fastapi_template": "test_project_backend",
                "FastAPI Template": "Test Project",
                "FastAPI Template with Authentication": "Test description",
                "Your Name": "Test Author",
                "your.email@example.com": "test@example.com",
            }
            customizer.docker_project_name = "test_project_backend"

            # Mock the methods that would normally process files
            with (
                patch.object(customizer, "get_files_to_process") as mock_get_files,
                patch.object(customizer, "process_file") as mock_process_file,
                patch.object(customizer, "update_env_file") as mock_update_env,
                patch.object(customizer, "create_customization_log") as mock_create_log,
                patch.object(customizer, "update_git_remote") as mock_update_git,
            ):
                mock_get_files.return_value = [custom_project_root / "README.md"]

                # Run the customization
                customizer.run()

                # Verify that all methods were called
                assert mock_get_files.called
                assert mock_process_file.called
                assert mock_update_env.called
                assert mock_create_log.called
                assert mock_update_git.called

    def test_directory_check_instructions_content(self):
        """Test that directory check provides clear instructions."""
        with patch.object(TemplateCustomizer, "__init__", lambda _self: None):
            customizer = TemplateCustomizer()
            customizer.project_root = self.project_root

            with (
                patch("builtins.print") as mock_print,
                patch("builtins.input", return_value="y"),
            ):
                # The script should exit when it detects template directory
                with pytest.raises(SystemExit) as exc_info:
                    customizer.verify_directory_name()

                # Verify exit code
                assert exc_info.value.code == 1

                # Verify that the instructions were printed
                printed_messages = [
                    call.args[0] for call in mock_print.call_args_list if call.args
                ]

                assert any(
                    "❌ Error: You're still in the 'fast-api-template' directory!"
                    in msg
                    for msg in printed_messages
                )
                assert any(
                    "This script should be run AFTER renaming the directory." in msg
                    for msg in printed_messages
                )
                assert any(
                    "Please run the rename script first:" in msg
                    for msg in printed_messages
                )
                assert any(
                    "./scripts/rename_template.sh" in msg for msg in printed_messages
                )


if __name__ == "__main__":
    pytest.main([__file__])
