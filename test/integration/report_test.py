import pytest

from pyprodtest import info
from test.integration.fixture.device import Device


@pytest.mark.integration
@info(name="Report Test", desc="Confirm reports are ok")
def test_reports(input, device: Device) -> None:
    assert input(
        "Will you check that the PDF and HTML contain correct info and formatting",
        bool,
    )
