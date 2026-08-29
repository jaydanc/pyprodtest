# In Progress

[See prototype here](https://github.com/jaydanc/pyprodtest/tree/prototype)

[See architecture here](/doc/design.md)

## Build Guide

uv pip install -e .
uv run ruff format --check .
uv run ruff check .
uv run pytest -p pyprodtest

PyProdTest always writes HTML, JSON, and CSV reports at the end of a run:
`pyprodtest-report.html`, `pyprodtest-report.json`, and
`pyprodtest-report.csv`. Report names are extensionless settings; each observer
adds its own extension. Use the report option to select another base path:

```powershell
uv run pytest -p pyprodtest --pyprodtest-report reports/device-acceptance
```

Tests can adjust the final report using the session-scoped `report` fixture.
The latest settings at session shutdown are used:

```python
def test_configure_report(report):
    report.path = "reports"
    report.name = "device-acceptance"
    report.enabled = True
```

Set `report.enabled = False` to suppress report generation for that run.

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
of opening a new one. Use `--pyprodtest-webui-host` and
`--pyprodtest-webui-port` to expose a different endpoint; port `0` selects a
free port but cannot reuse a tab between runs.
Use `--no-pyprodtest-webui` for a headless run.

## Test order

PyProdTest runs and displays tests in pytest's final collection order. Tests in
one module are normally collected in definition order. For an explicit
production plan, create `pyprodtest.yaml` in the pytest project root:

```yaml
tests:
  - test/integration/serial_test.py
  - test/integration/status_light_test.py
  - test/test_observers.py::test_html_observer_reports_lifecycle_and_escapes_content
```

Entries can name a whole test file, class, test function, or parametrized node
ID. Only listed tests are run, in plan order. An entry that matches no collected
tests is reported as an error so misspelled production tests are not silently
skipped. Use `--pyprodtest-plan PATH` for a differently named or located plan.
Node IDs can be inspected with `uv run pytest --collect-only -q`.
Use `--pyprodtest-ignore-plan` when running the repository's complete
development or unit-test suite.

PyProdTest also streams `INFO` and higher log messages to the terminal during a
run. Users can still select another threshold with pytest's
`--log-cli-level=LEVEL` option.
