import logging
from datetime import datetime

import pytest

from pyprodtest import info

LOGGER = logging.getLogger(__name__)


@pytest.mark.integration
@info(name="DUT Input Check", desc="Check we can accept a DUT")
def test_dut(input, dut, report) -> None:
    dut(input("Enter the DUT identifier for this test run"))
    # use time to get timestamp in YYMMDD-HHMMSS format for report output
    time_now = datetime.now().strftime("%Y%m%d-%H%M%S")
    report.path = f"reports/{report.dut_id}"
    report.name = f"report_{report.dut_id}_{time_now}"
    assert input("Is the DUT updated on the UI?", bool)
