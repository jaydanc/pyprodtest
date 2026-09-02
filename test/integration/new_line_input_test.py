import pytest

from pyprodtest import info
from test.integration.fixture.device import Device


@pytest.mark.integration
@info(
    name="New Line Input Check",
    desc="Check we can display line breaks from an input",
)
def test_serial_new_line(input, report, device: Device) -> None:
    assert input("Is this \n on a different \n line?", bool)
