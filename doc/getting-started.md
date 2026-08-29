# Getting started

## Requirements

- Python 3.13 or newer
- A [uv-managed project](https://docs.astral.sh/uv/)

## Install

Add PyProdTest from PyPI:

```powershell
uv add pyprodtest
```

To try the latest experimental build instead:

```powershell
uv add "pyprodtest @ git+https://github.com/jaydanc/pyprodtest.git@develop"
```

`uv add` records the dependency, updates the lockfile, and installs it into the
project environment. A separate global or editable installation is not needed.

## Create a test

```python title="test/test_device.py"
from pyprodtest import info, step


@info("Identify device", "Record the unit under test")
@step("Enter the serial number")
def test_serial_number(input) -> None:
    serial = input("Device serial number")
    assert serial.strip()
```

## Run it

```powershell
uv run pytest
```

pytest discovers PyProdTest automatically through its plugin entry point. The
browser opens at `http://127.0.0.1:8765`, and reports are written after the test
session ends.

## Add a project configuration

Create `pyprodtest.yaml` beside your project's `pyproject.toml`:

```yaml
name: Device acceptance

tests:
  - test/test_device.py
```

Continue with [writing tests](writing-tests.md) or see every
[configuration option](configuration.md).
