import logging

import pytest

from pyprodtest import info
from test.integration.fixture.device import Device


@pytest.mark.integration
@info(name="Bool Input Check", desc="Confirm we can accept a boolean input")
def test_status_light(input, device: Device) -> None:
    assert device.serial is not None
    logging.info("Checking status light for device %s", device.serial)
    assert input("Is the status light green? (Yes)", bool) is True
