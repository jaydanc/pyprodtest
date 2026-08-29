import time

from pyprodtest import info, req, step
from test.integration.fixture.device import Device


@info(name="Chart Test", desc="Test the chart functionality")
@req("REQ-1234")
@step("Run the chart test")
def test_chart(input, report, device: Device, measure) -> None:
    for i in range(20):
        measure(i, "iteration")
        time.sleep(1)

    plot = measure.plot("2d plot")
    for i in range(5):
        for j in range(5):
            plot.add(i, j)
            time.sleep(1)
