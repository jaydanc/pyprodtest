import logging
import time

import pytest

from pyprodtest import info


@pytest.mark.integration
@info(name="Sensor Accuracy", desc="Test the sensor accuracy")
def test_chart(measure) -> None:
    for i in range(5):
        base_val = 30
        if i % 2 == 0:
            base_val += 1
        else:
            base_val -= 1

        logging.info(f"Angle {base_val}")
        measure(base_val, "Angle", "deg")
        time.sleep(1)

    for i in range(5):
        base_val = 21
        if i % 2 == 0:
            base_val += 1
        else:
            base_val -= 1

        logging.info(f"Temperature {base_val}")
        measure(base_val, "Temperature", "deg C")
        time.sleep(1)

    plot = measure.plot("Temperature/Angle", x_unit="deg C", y_unit="deg")
    temperature = 21
    angle = 30
    for i in range(10):
        temperature += 1
        angle += 5
        plot.add(temperature, angle)
        time.sleep(1)
