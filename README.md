# PyProdTest

PyProdTest is an early-stage pytest plugin for running production tests. It adds
test metadata, operator prompts, a live browser view, ordered test plans, and
HTML, JSON, CSV, and PDF reports.

See the [architecture notes](doc/design.md) for the current design and known
diagram gaps. The earlier prototype is available on the
[`prototype` branch](https://github.com/jaydanc/pyprodtest/tree/prototype).

## Add to a uv project

From an existing Python 3.13+ uv project, add the published package:

```powershell
uv add pyprodtest
uv run pytest
```

pytest discovers the installed plugin through its `pytest11` entry point, so no
extra plugin flag is needed. Until the first PyPI release, add a checkout
directly instead:

```powershell
uv add "pyprodtest @ git+https://github.com/jaydanc/pyprodtest.git"
```

The live operator page opens automatically at `http://127.0.0.1:8765`. At the
end of the run, PyProdTest writes timestamped HTML, JSON, CSV, and PDF reports.

## Add production-test metadata

Decorators are optional and may be combined:

```python
from pyprodtest import info, req, step


@info("Status light", "Confirm the device is ready")
@req("REQ-42")
@step("Check that the status light is green")
def test_status_light(input) -> None:
    assert input("Is the status light green?", bool)
```

Use `input(prompt)` for text or `input(prompt, bool)` for a yes/no response.
The live UI handles prompts when enabled; otherwise PyProdTest uses the
console.

## Configure a run

Create `pyprodtest.yaml` in the pytest project root:

```yaml
name: Device acceptance

ui:
  enabled: true
  host: 127.0.0.1
  port: 8765

reports:
  output: reports/device-acceptance
  html: true
  json: true
  csv: false
  pdf: true

tests:
  - test/integration/serial_test.py
  - test/integration/status_light_test.py
```

`tests` accepts file paths and pytest node IDs. Only matching tests run, in the
listed order; an unmatched entry is an error. Use
`uv run pytest --collect-only -q` to inspect node IDs.

The extensionless `reports.output` value receives a session timestamp and each
enabled report extension. Set `ui.port` to `0` to choose a free port, or set
`ui.enabled` to `false` for console-only operation.

## Adjust reporting from a test

The session-scoped `report` fixture can change the destination or disable all
reports for the current run:

```python
def test_identify_device(input, report) -> None:
    serial = input("Device serial number")
    report.path = f"reports/{serial}"
    report.name = "acceptance"
    report.enabled = True
```

The final fixture values are used when the session ends. Set
`report.enabled = False` to suppress report generation; the YAML format toggles
still select which formats are enabled.

PyProdTest also streams log messages at `INFO` and above. pytest's
`--log-cli-level=LEVEL` option overrides that default.

## Development

Clone the repository and use its locked `uv` environment:

```powershell
uv sync
uv run ruff format --check .
uv run ruff check .
uv run pytest -p pyprodtest
```

To test a local checkout from another uv project, use
`uv add --editable ../pyprodtest`. Maintainers can create the source and wheel
distributions with `uv build --no-sources`; publishing requires a configured
PyPI project and `uv publish` credentials.
