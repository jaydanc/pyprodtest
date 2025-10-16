from pyprodtest import *
import time

@Test("LED", "Ensure the LED can be toggled via GPIO")
@Req("REQ-FW-001", "REQ-FW-005")
@Step("Connect to the device via serial")
@Step("Send message to switch the LED GPIO on")
@Step("Operator confirms LED status")
def test_led(input):
    # Simulated device
    class FakeDevice:
        def __init__(self):
            self.led_on = False
        def set_gpio(self):
            self.led_on = True

    device = FakeDevice()
    device.set_gpio()

    led_reported_as_on = input("Did the LED turn on?")
    assert led_reported_as_on, "Operator reported LED did not turn on"

@Test("ADC", "Ensure the ADC can be measured")
@Req("REQ-FW-001", "REQ-FW-005")
@Step("Connect to the device via serial")
@Step("Retrieve ADC sample")
@Step("Confirm within range")
def test_adc(input, measure):
    # Simulated device
    class FakeDevice:
        def __init__(self):
            self.adc_val = 0
        def get_adc_val(self):
            return self.adc_val

    input("Are you ready?")

    device = FakeDevice()
    adc_value = device.get_adc_val()

    # At the end of the test, all measurements are validated
    # Any false validations == test fail.
    # Additionally, all measurements are plotted by time of measurement.
    for i in range(0, 100):
        time.sleep(0.5)
        measure(adc_value + i, units.VOLT, units.within(1, 5))
    
    # Can combine with traditional assertions too
    assert adc_value == 0, "ADC value unexpected"

