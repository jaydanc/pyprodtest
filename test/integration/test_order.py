import pytest

from pyprodtest import info
from test.integration.fixture.device import Device


@pytest.mark.integration
@info(name="Test Order", desc="Confirm order is ok")
def test_reports(input, device: Device) -> None:
    assert input(
        "Does the test order in yaml look followed? Tests not present in the yaml should still be executed.",
        bool,
    )
