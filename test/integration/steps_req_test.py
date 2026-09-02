import pytest

from pyprodtest import info, req, step


@pytest.mark.integration
@info(name="Report Test", desc="Confirm reports are ok")
@req("REQ-9998, REQ-9999, REQ-9999, REQ-9999, REQ-9999, REQ-9999")
@step("This is step one")
@step("This is step two")
@step("This is step three")
@step("This is step four")
@step("This is step five")
@step("This is step six")
@step("This is step seven")
@step("This is step eight")
@step("This is step nine")
@step("This is step ten")
@step("This is step 11")
@step("This is step 12")
@step("This is step 13")
@step("This is step 14")
def test_serial(input) -> None:
    assert input(
        "Can you see a list of steps and requirements? Do they dispay okay?", bool
    )
