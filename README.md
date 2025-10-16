# Quick Start
A pytest plugin to support production testing operations:

- Helps traceability by providing requirement links
- Web UI: live measurements and input
- Produces easy to digest test reports
- Headless to allow CI integration

And most importantly... simple!

## Example

**test_led.py**
```python
import pyprodtest
import device

# All decorators are optional and are pure metadata
@Test("LED", "Ensure the LED can be enabled and disabled via GPIO")
@Req("REQ-FW-001", "REQ-FW-005")
@Step("Connect to the device via serial")
@Step("Send a message to switch the LED GPIO on")
@Step("Operator reports LED status")
def test_led(input):
    # Setup
    device = device_serial.connect()

    # Execute
    device.set_gpio(device.LED_PIN)

    # Assert
    led_reported_as_on = input("Did the LED turn on?")
    assert led_reported_as_on, "LED did not turn on"

@Test("ADC", "Ensure the ADC can be measured")
def test_adc(input, measure):
    device = device_serial.connect()
    adc_value = device.get_adc_val()

    # All measured values are updated on the chart in real-time
    # At the end of the test, all measurements are validated
    # Any false validations == test fail.
    measure(adc_value, units.VOLT, units.within(1, 5))
    
    # Can combine with traditional assertions
    assert adc_value == 0, "ADC value unexpected"

```

**Run:** `uv run pytest -p pyprodtest`

**Output**:

![alt text](/doc/res/operator_input.png)

Input example

![alt text](/doc/res/report_output.png)

Success output

![alt text](/doc/res/report_output_fail.png)

Failure output

![alt text](/doc/res/live_measurement.png)

Measuring incrementing value from 0-100

![alt text](/doc/res/live_measurement_500ms.png)

Measuring incrementing value from 0-100 with 0.5ms delay

---

# Further Reading

# Ideas

**Session State**

Sharing instances between tests can be quite helpful.
Forcing restrictive classes isn't great though.
Luckily, pytest has fixtures we can use for this:

```python
class Device:
    def __init__(self):
        print("Starting device...")
    def stop(self):
        print("Stopping device...")
```

Take this as a common Device class. A fixtures.py file would then exist which describes how this is passed to the test:

```python
@pytest.fixture(scope="session")
def device():
    svc = Device()
    yield svc
    svc.stop()
```

And in our test we can do:

```python
def test_one(device):
    assert isinstance(device, Device)
```


This treats the adapter as it should be treated, allowing us to have clean OOP style models. It also gives us control over their lifetime:
Possible values for scope are: function, class, module, package or session.

Fixtures with a variety of instantiation argument are hardly fixtures, but none the less, factory functions can be used to achieve this:

```python
@pytest.fixture
def device():
    """Factory fixture that lets tests instantiate devices with custom ids."""
    def _create(id):
        dev = Device(id)
        return dev
    return _create

def test_device_a(device):
    dev = device("ABC123")
    assert dev.id == "ABC123"

def test_device_b(device):
    dev = device("XYZ999")
    assert "XYZ" in dev.id
```

---

**Input Sets**

```python
@pytest.mark.parametrize("device", ["ABC123", "XYZ999"], indirect=True)
def test_led(device):
    print(f"Testing LED on {device}")
    assert len(device) > 0
```

```python
test_device.py::test_led[ABC123] PASSED
test_device.py::test_led[XYZ999] PASSED
```

Putting the parametrize decorator above the tests will allow you to repeat tests with input sets.

# Temp Dev

Running the prototype:

- uv pip install -e .
- uv run pytest -p pyprodtest --ui
- Navigate to localhost:5000 if not opened already
- See pyprodtest_report.json for capture evidence