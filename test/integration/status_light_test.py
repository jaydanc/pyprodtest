import logging

from pyprodtest import info, req, step
from test.integration.fixture.device import Device


@info(name="Status light", desc="Confirm the device status indicator")
@req("REQ-5678")
@step("Confirm the device serial was recorded")
@step("Confirm the status light is green")
def test_status_light(input, device: Device) -> None:
    assert device.serial is not None
    logging.info("Checking status light for device %s", device.serial)
    assert input("Is the status light green?", bool) is True
