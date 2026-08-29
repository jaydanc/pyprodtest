import logging
from time import sleep

from pyprodtest import info, step
from test.integration.fixture.device import Device


@info(name="Diagnostics", desc="Run device diagnostics")
@step("Run diagnostic checks")
def test_diagnostics(device: Device) -> None:
    assert device.serial is not None
    logging.info("Starting diagnostics for device %s", device.serial)
    sleep(5)
    logging.info("Diagnostic value: %s", 42)
    sleep(5)
    logging.info("Diagnostic value: %s", 43)
