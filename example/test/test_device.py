import logging

from pyprodtest import info, req, step


@info("Identify device", "Record the unit under test")
@req("DEMO-001")
@step("Enter the device serial number")
def test_identify_device(input, report) -> None:
    serial = input("Device serial number")
    report.path = f"reports/{serial}"
    report.name = "device-check"
    assert serial.strip()


@info("Status light", "Confirm that the device is ready")
@req("DEMO-002")
@step("Check that the status light is green")
def test_status_light(input) -> None:
    logging.info("Waiting for the operator to check the status light")
    assert input("Is the status light green?", bool)
