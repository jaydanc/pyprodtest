from pyprodtest import info, req, step
from test.integration.fixture.device import Device


@info(name="Serial number", desc="Identify the device under test")
@req("REQ-1234")
@step("Enter the device serial number")
def test_serial(input, report, device: Device) -> None:
    device.serial = input("Enter the device serial number")
    report.path = f"reports/{device.serial}"
    report.name = f"report-{device.serial}"
    assert device.serial
