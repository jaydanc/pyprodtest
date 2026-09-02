import logging
from time import sleep

import pytest

from pyprodtest import info
from test.integration.fixture.device import Device


@pytest.mark.integration
@info(name="Diagnostics", desc="Run device diagnostics")
def test_diagnostics(device: Device) -> None:
    assert device.serial is not None
    logging.info("Starting diagnostics for device %s", device.serial)
    sleep(5)
    logging.info("Diagnostic value: %s", 42)
    sleep(5)
    logging.info("Diagnostic value: %s", 43)
