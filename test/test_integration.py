import logging

from pyprodtest import info, req, step


@info(name="Test One", desc="This is the first test")
def test_one():
    logging.getLogger(__name__).info("Test One diagnostic value: %s", 42)
    assert True


def test_inputs(input):
    assert input("Enter SN-1234 for the serial number").lower() == "sn-1234"
    assert input("Is the status light green? Answer yes", bool) is True


@info(name="Test Two", desc="This is the second test")
@req("REQ-1234", "REQ-5678")
@step("Do this")
def test_two():
    assert False
