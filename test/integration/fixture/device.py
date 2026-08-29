"""Shared fixtures for the example production test sequence."""

from dataclasses import dataclass

import pytest


@dataclass
class Device:
    """Device state gathered and shared across the production test run."""

    serial: str | None = None


@pytest.fixture(scope="session")
def device() -> Device:
    """Return the device under test for the current production session."""
    return Device()
