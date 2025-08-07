"""Test CI validation script functionality."""

import os
import sys
from pathlib import Path


def test_validate_ci_script_exists() -> None:
    """Test that the CI validation script exists and is executable."""
    script_path = Path("scripts/validate_ci.sh")
    assert script_path.exists(), "CI validation script should exist"
    assert os.access(script_path, os.X_OK), "CI validation script should be executable"


def test_requirements_dev_exists() -> None:
    """Test that development requirements file exists."""
    requirements_path = Path("requirements-dev.txt")
    assert requirements_path.exists(), "requirements-dev.txt should exist"


def test_git_hooks_script_exists() -> None:
    """Test that git hooks setup script exists and is executable."""
    script_path = Path("scripts/setup-git-hooks.sh")
    assert script_path.exists(), "Git hooks setup script should exist"
    assert os.access(
        script_path,
        os.X_OK,
    ), "Git hooks setup script should be executable"


def test_pre_commit_config_updated() -> None:
    """Test that pre-commit config has been updated with correct versions."""
    config_path = Path(".pre-commit-config.yaml")
    assert config_path.exists(), "Pre-commit config should exist"

    with config_path.open() as f:
        content = f.read()

    # Check for updated versions
    assert "rev: 25.1.0" in content, "Black should be version 25.1.0"
    assert "rev: v1.17.0" in content, "Mypy should be version v1.17.0"
    assert "rev: v0.4.0" in content, "Ruff should be version v0.4.0"


def test_mypy_config_updated() -> None:
    """Test that mypy config has been updated with transformers ignore."""
    config_path = Path("mypy.ini")
    assert config_path.exists(), "Mypy config should exist"

    with config_path.open() as f:
        content = f.read()

    # Check for transformers ignore
    assert "[mypy-transformers.*]" in content, "Mypy config should ignore transformers"
    assert (
        "ignore_missing_imports = True" in content
    ), "Mypy config should have ignore_missing_imports"


def test_ci_validation_docs_exist() -> None:
    """Test that CI validation documentation exists."""
    docs_path = Path("docs/troubleshooting/ci-validation-workflow.md")
    assert docs_path.exists(), "CI validation documentation should exist"


def test_validation_script_has_virtual_env_detection() -> None:
    """Test that validation script includes virtual environment detection."""
    script_path = Path("scripts/validate_ci.sh")

    with script_path.open() as f:
        content = f.read()

    # Check for virtual environment detection
    assert "venv" in content, "Script should detect venv directory"
    assert ".venv" in content, "Script should detect .venv directory"
    assert (
        "source venv/bin/activate" in content
    ), "Script should activate virtual environment"


if __name__ == "__main__":
    # Run tests
    test_functions = [
        test_validate_ci_script_exists,
        test_requirements_dev_exists,
        test_git_hooks_script_exists,
        test_pre_commit_config_updated,
        test_mypy_config_updated,
        test_ci_validation_docs_exist,
        test_validation_script_has_virtual_env_detection,
    ]

    passed = 0
    failed = 0

    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except Exception:
            failed += 1

    if failed > 0:
        sys.exit(1)
    else:
        pass
