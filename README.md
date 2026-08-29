# In Progress

[See prototype here](https://github.com/jaydanc/pyprodtest/tree/prototype)

[See architecture here](/doc/design.md)

## Build Guide

uv pip install -e .
uv run ruff format --check .
uv run ruff check .
uv run pytest -p pyprodtest

PyProdTest writes HTML, JSON, and CSV reports at the end of a run by default,
such as `pyprodtest-report-20260829-140507.html`, `.json`, and `.csv`. A session
timestamp is appended to the configured extensionless name, then each observer
adds its own extension.
Configure the output and formats in `pyprodtest.yaml`:

```yaml
reports:
  output: reports/device-acceptance
  html: true
  json: true
  csv: false
```

Tests can adjust the final report using the session-scoped `report` fixture.
The latest settings at session shutdown are used:

```python
def test_configure_report(report):
    report.path = "reports"
    report.name = "device-acceptance"
    report.enabled = True
```

Set `report.enabled = False` to suppress all report generation dynamically for
that run. The YAML format toggles remain the normal project-level settings.

## Operator input

Tests can request the `input` fixture to collect text from an operator. Outside
of live web mode, input is read from the console:

```python
def test_serial_number(input):
    serial_number = input("Enter the serial number")
    assert serial_number.startswith("SN-")
```

Pass `bool` as the optional input type to ask for a yes/no decision. The console
acceptor recognizes `y`, `yes`, `n`, and `no`:

```python
def test_status_light(input):
    assert input("Is the status light green?", bool)
```

The plugin owns acceptor selection so tests use the same fixture in console and
live web runs.

## Live web UI

PyProdTest opens an operator page in the default browser automatically. The
page shows collection and execution state, captured logs, and any operator
input request. It updates automatically while pytest is running.

```powershell
uv run pytest -p pyprodtest
```

By default the server listens only on `127.0.0.1` at port `8765`. The page keeps
reconnecting between runs, so PyProdTest reuses an existing browser tab instead
of opening a new one. Configure the UI in `pyprodtest.yaml`; port `0` selects a
free port but cannot reuse a tab between runs:

```yaml
ui:
  enabled: true
  host: 127.0.0.1
  port: 8765
```

## Test order

PyProdTest runs and displays tests in pytest's final collection order. Tests in
one module are normally collected in definition order. For an explicit
production plan, create `pyprodtest.yaml` in the pytest project root:

```yaml
name: Device acceptance
ui:
  enabled: true
reports:
  output: pyprodtest-report
  html: true
  json: true
  csv: true
tests:
  - test/integration/serial_test.py
  - test/integration/status_light_test.py
  - test/test_observers.py::test_html_observer_reports_lifecycle_and_escapes_content
```

The optional `name` is shown as the live UI heading and browser-tab title. If
omitted, the UI uses `Production test execution`.

Entries can name a whole test file, class, test function, or parametrized node
ID. Only listed tests are run, in plan order. An entry that matches no collected
tests is reported as an error so misspelled production tests are not silently
skipped. Node IDs can be inspected with `uv run pytest --collect-only -q`.

All PyProdTest project settings live in `pyprodtest.yaml`; the plugin does not
register equivalent command-line options.

PyProdTest also streams `INFO` and higher log messages to the terminal during a
run. Users can still select another threshold with pytest's
`--log-cli-level=LEVEL` option.
