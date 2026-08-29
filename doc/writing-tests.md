# Writing production tests

PyProdTest tests remain ordinary pytest tests. Fixtures, parametrization,
assertions, logging, setup, call, and teardown behavior continue to work as
pytest defines them.

## Add human-readable metadata

```python
from pyprodtest import info, req, step


@info("Output voltage", "Verify the regulated 5 V rail")
@req("POWER-12", "SAFETY-03")
@step("Connect the calibrated meter")
@step("Measure the output voltage")
def test_output_voltage(device) -> None:
    assert 4.9 <= device.output_voltage() <= 5.1
```

- `info(name, desc)` sets the displayed test name and description.
- `req(*requirements)` records requirement identifiers.
- `step(*steps)` records instructions in source order. It may be stacked.

All decorators are optional.

## Ask for operator input

Request text with the `input` fixture:

```python
def test_serial_number(input) -> None:
    serial = input("Device serial number")
    assert serial.startswith("SN-")
```

Pass `bool` for a yes/no decision:

```python
def test_enclosure(input) -> None:
    assert input("Is the enclosure undamaged?", bool)
```

With the web UI enabled, the prompt appears in the browser. With it disabled,
the console accepts `y`, `yes`, `n`, or `no`. The fixture blocks the current
test until the operator responds.

## Stream measured data

Call the `measure` fixture to record a value against the current timestamp:

```python
def test_output_voltage(device, measure) -> None:
    for _ in range(20):
        voltage = device.output_voltage()
        measure(voltage, "Voltage")
```

The operator console shows the latest value and updates its Chart.js time-series
chart while the test runs. For data where X is not time, create an explicit plot:

```python
def test_calibration(device, measure) -> None:
    calibration = measure.plot("Calibration")
    for dac_value in range(10):
        calibration.add(dac_value, device.output_voltage())
```

## Capture diagnostics

Use standard Python logging:

```python
import logging


def test_connection(device) -> None:
    logging.info("Connecting to %s", device.serial)
    assert device.is_connected()
```

PyProdTest captures the timestamp, level, logger name, and message in reports
and streams `INFO` and higher to the terminal by default. Override the terminal
threshold with pytest's `--log-cli-level=LEVEL` option.

## Test ordering

Without a configured plan, pytest's final collection order is used. For an
explicit production sequence, list paths or node IDs under `tests` in
`pyprodtest.yaml`. PyProdTest selects only those tests and preserves the listed
order.

Use this to inspect node IDs:

```powershell
uv run pytest --collect-only -q
```

An entry that matches no collected test raises an error, preventing a misspelled
production test from being silently skipped.
