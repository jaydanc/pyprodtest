from pyprodtest import info, req, step
from test.integration.fixture.device import Device


@info(name="Failure example", desc="Demonstrate a failed production test")
@req("REQ-9999")
@step("Run the intentional failure")
def test_failure(device: Device) -> None:
    assert device.serial is not None
    assert False, "Intentional integration-test failure"
