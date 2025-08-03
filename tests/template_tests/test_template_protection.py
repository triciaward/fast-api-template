"""Tests for template protection features."""

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add scripts directory to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))


class TestPreventTemplatePush:
    """Test the prevent_template_push.py script functionality."""

    def test_script_exists_and_executable(self):
        """Test that the prevent_template_push.py script exists and is executable."""
        script_path = Path("scripts/prevent_template_push.py")
        assert script_path.exists(), "prevent_template_push.py should exist"
        assert os.access(script_path, os.X_OK), "Script should be executable"

    def test_script_imports_correctly(self):
        """Test that the script can be imported without errors."""
        try:
            from prevent_template_push import (
                get_remote_url,
                is_template_repository,
                main,
            )

            assert callable(get_remote_url)
            assert callable(is_template_repository)
            assert callable(main)
        except ImportError as e:
            pytest.fail(f"Failed to import prevent_template_push: {e}")

    @patch("prevent_template_push.subprocess.run")
    def test_get_remote_url_success(self, mock_run):
        """Test getting remote URL successfully."""
        from prevent_template_push import get_remote_url

        mock_run.return_value = MagicMock(
            stdout="https://github.com/user/repo.git\n", returncode=0
        )

        result = get_remote_url()
        assert result == "https://github.com/user/repo.git"
        mock_run.assert_called_once_with(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )

    @patch("prevent_template_push.subprocess.run")
    def test_get_remote_url_failure(self, mock_run):
        """Test getting remote URL when git command fails."""
        from prevent_template_push import get_remote_url

        mock_run.side_effect = subprocess.CalledProcessError(
            1, "git remote get-url origin"
        )

        result = get_remote_url()
        assert result is None

    def test_is_template_repository_detection(self):
        """Test template repository detection logic."""
        from prevent_template_push import is_template_repository

        # Test template repository URLs
        template_urls = [
            "https://github.com/triciaward/fast-api-template.git",
            "git@github.com:triciaward/fast-api-template.git",
            "https://github.com/user/fast-api-template.git",
            "https://github.com/user/fastapi-template.git",
            "git@github.com:user/fast-api-template.git",
        ]

        for url in template_urls:
            assert is_template_repository(url), f"Should detect template repo: {url}"

        # Test non-template repository URLs
        non_template_urls = [
            "https://github.com/user/my-project.git",
            "git@github.com:user/my-awesome-api.git",
            "https://github.com/user/todo-app-backend.git",
            "https://github.com/user/ecommerce-api.git",
        ]

        for url in non_template_urls:
            assert not is_template_repository(
                url
            ), f"Should not detect template repo: {url}"

    def test_is_template_repository_none_input(self):
        """Test template repository detection with None input."""
        from prevent_template_push import is_template_repository

        assert not is_template_repository(None)
        assert not is_template_repository("")

    @patch("prevent_template_push.Path.exists")
    @patch("prevent_template_push.get_remote_url")
    @patch("prevent_template_push.is_template_repository")
    @patch("builtins.input")
    def test_main_not_in_git_repo(
        self, mock_input, mock_is_template, mock_get_remote, mock_exists
    ):
        """Test main function when not in a git repository."""
        from prevent_template_push import main

        mock_exists.return_value = False

        result = main()
        assert result == 0
        mock_get_remote.assert_not_called()
        mock_is_template.assert_not_called()
        mock_input.assert_not_called()

    @patch("prevent_template_push.Path.exists")
    @patch("prevent_template_push.get_remote_url")
    @patch("prevent_template_push.is_template_repository")
    @patch("builtins.input")
    def test_main_non_template_repo(
        self, mock_input, mock_is_template, mock_get_remote, mock_exists
    ):
        """Test main function with non-template repository."""
        from prevent_template_push import main

        mock_exists.return_value = True
        mock_get_remote.return_value = "https://github.com/user/my-project.git"
        mock_is_template.return_value = False

        result = main()
        assert result == 0
        mock_input.assert_not_called()

    @patch("prevent_template_push.Path.exists")
    @patch("prevent_template_push.get_remote_url")
    @patch("prevent_template_push.is_template_repository")
    @patch("builtins.input")
    def test_main_template_repo_user_continues(
        self, mock_input, mock_is_template, mock_get_remote, mock_exists
    ):
        """Test main function with template repository when user chooses to continue."""
        from prevent_template_push import main

        mock_exists.return_value = True
        mock_get_remote.return_value = (
            "https://github.com/triciaward/fast-api-template.git"
        )
        mock_is_template.return_value = True
        mock_input.return_value = "y"

        result = main()
        assert result == 0
        mock_input.assert_called_once()

    @patch("prevent_template_push.Path.exists")
    @patch("prevent_template_push.get_remote_url")
    @patch("prevent_template_push.is_template_repository")
    @patch("builtins.input")
    def test_main_template_repo_user_cancels(
        self, mock_input, mock_is_template, mock_get_remote, mock_exists
    ):
        """Test main function with template repository when user cancels."""
        from prevent_template_push import main

        mock_exists.return_value = True
        mock_get_remote.return_value = (
            "https://github.com/triciaward/fast-api-template.git"
        )
        mock_is_template.return_value = True
        mock_input.return_value = "n"

        result = main()
        assert result == 1
        mock_input.assert_called_once()


class TestGitHooks:
    """Test git hooks for template protection."""

    def test_git_hook_script_exists(self):
        """Test that the git hook script exists and is executable."""
        hook_path = Path("scripts/git-hooks/pre-commit")
        assert hook_path.exists(), "Git hook script should exist"
        assert os.access(hook_path, os.X_OK), "Git hook script should be executable"

    def test_git_hook_script_content(self):
        """Test that the git hook script contains required logic."""
        with open("scripts/git-hooks/pre-commit") as f:
            content = f.read()

        # Check for required elements
        assert "fast-api-template" in content, "Should check for template repository"
        assert "CRITICAL WARNING" in content, "Should display warning message"
        assert "read -p" in content, "Should prompt user for confirmation"
        assert "exit 1" in content, "Should exit with error code on cancel"

    def test_install_git_hooks_script_exists(self):
        """Test that the install git hooks script exists and is executable."""
        script_path = Path("scripts/install_git_hooks.sh")
        assert script_path.exists(), "install_git_hooks.sh should exist"
        assert os.access(script_path, os.X_OK), "Script should be executable"

    def test_install_git_hooks_script_content(self):
        """Test that the install script contains required commands."""
        with open("scripts/install_git_hooks.sh") as f:
            content = f.read()

        assert "cp scripts/git-hooks/pre-commit" in content, "Should copy hook script"
        assert "chmod +x" in content, "Should make hook executable"
        assert "Protection enabled" in content, "Should confirm installation"

    @pytest.mark.skipif(
        not Path(".git").exists(),
        reason="Not in a git repository",
    )
    def test_git_hooks_can_be_installed(self):
        """Test that git hooks can be installed successfully."""
        # This test requires being in a git repository
        result = subprocess.run(
            ["./scripts/install_git_hooks.sh"],
            capture_output=True,
            text=True,
        )

        # Should succeed and show success message
        assert result.returncode == 0, f"Install script failed: {result.stderr}"
        assert "Git hooks installed successfully" in result.stdout


class TestPreCommitConfiguration:
    """Test pre-commit configuration for template protection."""

    def test_precommit_config_has_template_protection(self):
        """Test that pre-commit config includes template protection hook."""
        import yaml

        with open(".pre-commit-config.yaml") as f:
            config = yaml.safe_load(f)

        # Find the local repo with template protection
        template_hook_found = False
        for repo in config["repos"]:
            if repo.get("repo") == "local":
                for hook in repo.get("hooks", []):
                    if hook.get("id") == "prevent-template-push":
                        template_hook_found = True
                        assert "commit" in hook.get(
                            "stages", []
                        ), "Should run on commit"
                        assert "push" in hook.get("stages", []), "Should run on push"
                        assert "prevent_template_push.py" in hook.get(
                            "entry", ""
                        ), "Should use our script"
                        break

        assert template_hook_found, "Template protection hook should be configured"


class TestDocumentationWarnings:
    """Test that documentation includes template protection warnings."""

    def test_readme_has_template_protection_warnings(self):
        """Test that README.md includes template protection warnings."""
        with open("README.md") as f:
            content = f.read()

        # Check for critical warning section
        assert "CRITICAL: Create a New GitHub Repository First" in content
        assert "🚨 IMPORTANT:" in content
        assert "fast-api-template" in content
        assert "git remote set-url origin" in content

    def test_template_readme_has_protection_warnings(self):
        """Test that TEMPLATE_README.md includes template protection warnings."""
        with open("docs/TEMPLATE_README.md") as f:
            content = f.read()

        # Check for critical warning section
        assert "CRITICAL: Create a New GitHub Repository First" in content
        assert "🚨 IMPORTANT:" in content
        assert "fast-api-template" in content
        assert "git remote set-url origin" in content

    def test_getting_started_has_protection_warnings(self):
        """Test that getting-started.md includes template protection warnings."""
        with open("docs/tutorials/getting-started.md") as f:
            content = f.read()

        # Check for critical warning section
        assert "CRITICAL: Create a New GitHub Repository First" in content
        assert "🚨 IMPORTANT:" in content
        assert "fast-api-template" in content
        assert "git remote set-url origin" in content

    def test_documentation_mentions_safety_features(self):
        """Test that documentation mentions the safety features."""
        files_to_check = [
            "README.md",
            "docs/TEMPLATE_README.md",
            "docs/tutorials/getting-started.md",
        ]

        for file_path in files_to_check:
            with open(file_path) as f:
                content = f.read()

            # Check for safety features mention
            assert "🛡️ Safety Features" in content or "🛡️ Safety Feature" in content
            assert "pre-commit hooks" in content

            # Check for git hooks mention (may be in different forms)
            git_hooks_mentioned = (
                "git hooks" in content.lower()
                or "git-hooks" in content.lower()
                or "install_git_hooks" in content.lower()
            )
            assert git_hooks_mentioned, f"Git hooks should be mentioned in {file_path}"


class TestIntegration:
    """Integration tests for template protection."""

    @pytest.mark.skipif(
        not Path(".git").exists(),
        reason="Not in a git repository",
    )
    def test_template_protection_workflow(self):
        """Test the complete template protection workflow."""
        # This test simulates what happens when someone tries to commit
        # to the template repository

        # First, install the git hooks
        result = subprocess.run(
            ["./scripts/install_git_hooks.sh"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, "Should install git hooks successfully"

        # Check that the hook was installed
        hook_path = Path(".git/hooks/pre-commit")
        assert hook_path.exists(), "Git hook should be installed"
        assert os.access(hook_path, os.X_OK), "Git hook should be executable"

        # Test that the prevent_template_push.py script can be run
        result = subprocess.run(
            [sys.executable, "scripts/prevent_template_push.py"],
            capture_output=True,
            text=True,
        )
        # Should not crash and should return 0 or 1 depending on repository
        assert result.returncode in [
            0,
            1,
        ], f"Script should exit with 0 or 1, got {result.returncode}"
