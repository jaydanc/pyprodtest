"""Project-level pytest configuration."""

import pytest


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Run the integration test module before the rest of the test suite."""
    integration_test = config.rootpath / "test" / "test_integration.py"
    items.sort(key=lambda item: item.path != integration_test)
