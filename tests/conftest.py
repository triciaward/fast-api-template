"""
Global test configuration and fixtures.

This file is automatically loaded by pytest and provides:
- Global fixtures available to all tests
- Test configuration and setup
- Automatic exclusion of template-specific tests
"""

import pytest


def pytest_configure(config):
    """Configure pytest to exclude template tests by default."""
    # Register the template_only marker
    config.addinivalue_line(
        "markers",
        "template_only: marks tests as template-specific (excluded by default)",
    )

    # Set default marker expression to exclude template tests
    # This only applies if no explicit marker filtering is provided
    if not config.getoption("markexpr"):
        config.option.markexpr = "not template_only"


def pytest_collection_modifyitems(config, items):
    """Modify test collection to exclude template tests by default."""
    # Only apply if no explicit marker filtering is provided
    if not config.getoption("markexpr"):
        for item in items:
            if "template_only" in item.keywords:
                item.add_marker(
                    pytest.mark.skip(reason="Template test excluded by default")
                )
