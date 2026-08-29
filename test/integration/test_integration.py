import logging
from time import sleep

import pytest

from pyprodtest import info, req, step


@pytest.fixture(scope="session")
def device():
    logging.info("Using device DEV-1234")
    return "DEV-1234"


@info(name="Test One", desc="This is the first test")
def test_one():
    logging.getLogger(__name__).info("Test One diagnostic value: %s", 42)
    sleep(5)  # Simulate a long-running test
    logging.getLogger(__name__).info("Test One diagnostic value: %s", 43)
    sleep(5)  # Simulate a long-running test
    assert True


@info(name="Input Test", desc="This is the second test")
@req("REQ-1234", "REQ-5678")
@step("Ask for serial")
@step("Ask for status light")
def test_inputs(input, device):
    logging.info("Device is %s", device)
    logging.info("Device is %s", device)
    sleep(5)  # Simulate a long-running test
    assert input("Enter SN-1234 for the serial number").lower() == "sn-1234"
    assert input("Is the status light green? Answer yes", bool) is True


@info(name="Test Two", desc="This is the second test")
@req("REQ-1234", "REQ-5678")
@step("Do this")
def test_two():
    assert False
