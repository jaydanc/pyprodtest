import logging
import time

from pyprodtest import info, req, step
from test.integration.fixture.device import Device


@info(name="Sensor Accuracy", desc="Test the sensor accuracy")
@req("REQ-1234")
@step("Run the sensor accuracy test")
def test_chart(input, report, device: Device, measure) -> None:
    for i in range(5):
        base_val = 30
        if i % 2 == 0:
            base_val += 1
        else:
            base_val -= 1

        logging.info(f"Angle {base_val}")
        measure(base_val, "Angle")
        time.sleep(1)

    for i in range(5):
        base_val = 21
        if i % 2 == 0:
            base_val += 1
        else:
            base_val -= 1

        logging.info(f"Temperature {base_val}")
        measure(base_val, "Temperature")
        time.sleep(1)

    plot = measure.plot("Temperature/Angle")
    temperature = 21
    angle = 30
    for i in range(10):
        temperature += 1
        angle += 5
        plot.add(temperature, angle)
        time.sleep(1)
