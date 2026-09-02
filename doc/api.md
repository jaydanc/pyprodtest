# Public API

The supported import surface is deliberately small:

```python
from pyprodtest import info, req, step
```

## `info(name, desc)`

Adds a display name and description to a test function.

```python
@info("Serial number", "Identify the device under test")
def test_serial(): ...
```

## `req(*requirements)`

Adds one or more requirement identifiers.

```python
@req("REQ-100", "REQ-105")
def test_power(): ...
```

## `step(*steps)`

Adds one or more operator/test steps. Stacked decorators retain their visual
source order.

```python
@step("Connect the device")
@step("Apply power")
def test_startup(): ...
```

## pytest fixtures

The plugin also registers four fixtures. They are supplied by pytest rather than
imported from `pyprodtest`.

### `input`

```python
value: str = input("Device serial")
accepted: bool = input("Is the indicator green?", bool)
```

Supported types are `str` and `bool`.

### `dut`

Set the device under test identifier used by reports and the live UI:

```python
def test_identify(dut) -> None:
    dut("SN-1234")
```

### `report`

The session-scoped fixture exposes:

| Attribute | Meaning |
| --- | --- |
| `path` | Output directory |
| `name` | Extensionless report base name |
| `enabled` | Whether any reports are written |
| `dut_id` | Device under test identifier |

### `measure`

Record a numeric value against the current timestamp:

```python
def test_voltage(device, measure) -> None:
    measure(device.output_voltage(), "Voltage", "V")
```

The optional third argument is the unit displayed with the latest value and on
the chart axis. It must be a string, such as `"V"`, `"A"`, or `"deg"`.

Repeated calls with the same name append points to the same live chart. A test
can have multiple charts; give each series a different name:

```python
def test_power_rails(device, measure) -> None:
    measure(device.output_voltage(), "Output voltage", "V")
    measure(device.output_current(), "Output current", "A")
```

For an explicit numeric X axis, create a plot and add X/Y pairs:

```python
def test_calibration(device, measure) -> None:
    calibration = measure.plot("Calibration", x_unit="DAC", y_unit="V")
    calibration.add(0, device.output_voltage())
    calibration.add(128, device.output_voltage())
```

Values and explicit X coordinates must be real numbers. Explicit plots accept
independent `x_unit` and `y_unit` strings. The shorter
`measure.plot("Calibration", "V")` form remains available when only the Y unit
is needed. A name cannot be shared between a timestamped series and an explicit
X/Y plot, or reused with different axis units, within the same test.

Modules under `_pyprodtest` are private implementation details and may change
without preserving a public compatibility contract.
