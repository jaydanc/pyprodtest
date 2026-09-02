import pytest

from pyprodtest import info


@pytest.mark.integration
@info(name="Failure example", desc="Demonstrate a failed production test")
def test_failure(input) -> None:
    input("When this fails, check the error message looks okay and well formated", bool)
    assert False, "Intentional integration-test failure"
