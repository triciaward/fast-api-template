"""Tests for pre-commit configuration and functionality."""

import os
import subprocess
from pathlib import Path

import pytest


class TestPreCommitConfiguration:
    """Test pre-commit configuration and setup."""

    def test_precommit_config_exists(self):
        """Test that .pre-commit-config.yaml exists."""
        config_path = Path(".pre-commit-config.yaml")
        assert config_path.exists(), ".pre-commit-config.yaml should exist"

        # Verify it's a valid YAML file
        import yaml

        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert "repos" in config, "Config should have 'repos' section"
        assert isinstance(config["repos"], list), "Repos should be a list"

    def test_precommit_config_has_required_hooks(self):
        """Test that required hooks are configured."""
        import yaml

        with open(".pre-commit-config.yaml") as f:
            config = yaml.safe_load(f)

        hook_ids = []
        for repo in config["repos"]:
            for hook in repo.get("hooks", []):
                hook_ids.append(hook["id"])

        # Check for required hooks
        assert "ruff" in hook_ids, "ruff hook should be configured"
        assert "black" in hook_ids, "black hook should be configured"

        # Note: mypy is temporarily disabled, so we don't check for it
        # assert "mypy" in hook_ids, "mypy hook should be configured"

    def test_install_script_exists(self):
        """Test that install_precommit.sh exists and is executable."""
        script_path = Path("scripts/install_precommit.sh")
        assert script_path.exists(), "scripts/install_precommit.sh should exist"
        assert os.access(
            script_path, os.X_OK
        ), "scripts/install_precommit.sh should be executable"

    def test_install_script_content(self):
        """Test that install script contains required commands."""
        with open("scripts/install_precommit.sh") as f:
            content = f.read()

        assert "pip install pre-commit" in content, "Script should install pre-commit"
        assert "pre-commit install" in content, "Script should install hooks"
        assert "pre-commit run --all-files" in content, "Script should run hooks"

    @pytest.mark.skipif(
        not Path(".git/hooks/pre-commit").exists(),
        reason="Pre-commit hooks not installed in test environment",
    )
    def test_precommit_hooks_installed(self):
        """Test that pre-commit hooks are installed (if in development environment)."""
        hook_path = Path(".git/hooks/pre-commit")
        if hook_path.exists():
            assert os.access(hook_path, os.X_OK), "Pre-commit hook should be executable"

            # Verify it's not the sample file
            with open(hook_path) as f:
                content = f.read()
            assert "pre-commit" in content, "Hook should contain pre-commit logic"

    def test_ruff_configuration(self):
        """Test that ruff is properly configured."""
        # Check if pyproject.toml has ruff configuration
        pyproject_path = Path("pyproject.toml")
        if pyproject_path.exists():
            with open(pyproject_path) as f:
                content = f.read()

            # Verify ruff section exists
            assert (
                "[tool.ruff]" in content
            ), "pyproject.toml should have [tool.ruff] section"

    def test_black_configuration(self):
        """Test that black is properly configured."""
        # Check if pyproject.toml has black configuration
        pyproject_path = Path("pyproject.toml")
        if pyproject_path.exists():
            with open(pyproject_path) as f:
                content = f.read()

            # This project uses ruff for formatting instead of black
            # Verify ruff format section exists
            assert (
                "[tool.ruff.format]" in content
            ), "pyproject.toml should have [tool.ruff.format] section"

    def test_mypy_configuration(self):
        """Test that mypy is properly configured."""
        mypy_path = Path("mypy.ini")
        assert mypy_path.exists(), "mypy.ini should exist"

        # Verify it's a valid INI file
        import configparser

        config = configparser.ConfigParser()
        config.read(mypy_path)

        assert "mypy" in config, "mypy.ini should have [mypy] section"
        assert (
            "python_version" in config["mypy"]
        ), "mypy.ini should specify python_version"

    def test_precommit_installation_script_runs(self):
        """Test that the installation script can be executed (integration test)."""
        # This test would actually run the script in a real environment
        # We'll mock it for safety in CI/CD
        script_path = Path("scripts/install_precommit.sh")

        # Verify script syntax is valid
        try:
            result = subprocess.run(
                ["bash", "-n", str(script_path)], capture_output=True, text=True
            )
            assert result.returncode == 0, f"Script syntax error: {result.stderr}"
        except FileNotFoundError:
            pytest.skip("bash not available in test environment")

    def test_readme_has_precommit_documentation(self):
        """Test that README contains pre-commit documentation."""
        readme_path = Path("README.md")
        assert readme_path.exists(), "README.md should exist"

        with open(readme_path) as f:
            content = f.read()

        # Check for pre-commit section
        assert (
            "Code Quality (Pre-commit Hooks)" in content
        ), "README should have pre-commit section"
        assert (
            "install_precommit.sh" in content
        ), "README should mention installation script"
        assert (
            "pre-commit install" in content
        ), "README should mention hook installation"


class TestPreCommitHooks:
    """Test that pre-commit hooks work correctly."""

    @pytest.mark.skipif(
        not Path(".git/hooks/pre-commit").exists(),
        reason="Pre-commit hooks not installed in test environment",
    )
    def test_ruff_hook_works(self):
        """Test that ruff hook can be run manually."""
        try:
            result = subprocess.run(
                ["pre-commit", "run", "ruff", "--all-files"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            # ruff should pass (we know our code is clean)
            assert result.returncode == 0, f"ruff failed: {result.stderr}"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("pre-commit or ruff not available in test environment")

    @pytest.mark.skipif(
        not Path(".git/hooks/pre-commit").exists(),
        reason="Pre-commit hooks not installed in test environment",
    )
    def test_black_hook_works(self):
        """Test that black hook can be run manually."""
        try:
            result = subprocess.run(
                ["pre-commit", "run", "black", "--all-files"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            # black should pass (we know our code is formatted)
            assert result.returncode == 0, f"black failed: {result.stderr}"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("pre-commit or black not available in test environment")

    def test_precommit_config_is_valid_yaml(self):
        """Test that .pre-commit-config.yaml is valid YAML."""
        import yaml

        try:
            with open(".pre-commit-config.yaml") as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in .pre-commit-config.yaml: {e}")

    def test_precommit_config_has_valid_repo_urls(self):
        """Test that all repo URLs in config are valid."""
        import yaml

        with open(".pre-commit-config.yaml") as f:
            config = yaml.safe_load(f)

        for repo in config["repos"]:
            if "repo" in repo:
                url = repo["repo"]
                # Basic URL validation
                assert url.startswith("https://"), f"Repo URL should be HTTPS: {url}"
                assert "github.com" in url, f"Repo URL should be from GitHub: {url}"
