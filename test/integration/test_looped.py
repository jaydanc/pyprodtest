import pytest

from pyprodtest import info
from test.integration.fixture.device import Device


@pytest.mark.integration
@info(name="Test Looped", desc="Confirm looped execution of tests")
def test_reports(input, device: Device) -> None:
    assert input(
        "Set loop to true in config. Do we run twice and generate 2 unique reports?",
        bool,
    )
