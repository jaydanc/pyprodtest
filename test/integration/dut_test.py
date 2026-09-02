import logging

import pytest

from pyprodtest import info

LOGGER = logging.getLogger(__name__)


@pytest.mark.integration
@info(name="DUT Input Check", desc="Check we can accept a DUT")
def test_dut(input, dut) -> None:
    dut(input("Enter DUT ID"))
    assert input("Is the DUT updated on the UI?", bool)
