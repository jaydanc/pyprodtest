from pyprodtest import *

@info(name="Test One", desc="This is the first test")
def test_one():
    assert True

@info(name="Test Two", desc="This is the second test")
@req("REQ-1234", "REQ-5678")
@step("Do this")
def test_two():
    assert True