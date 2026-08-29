# In Progress

[See prototype here](https://github.com/jaydanc/pyprodtest/tree/prototype)

[See architecture here](/doc/design.md)

## Build Guide

uv pip install -e .
uv run ruff format --check .
uv run ruff check .
uv run pytest -p pyprodtest

HTML report generation:

```powershell
uv run pytest -p pyprodtest --pyprodtest-html pyprodtest-report.html
```

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

Run pytest with the web UI enabled to open an operator page in the default
browser. The page shows collection and execution state, captured logs, and any
operator input request. It updates automatically while pytest is running.

```powershell
uv run pytest -p pyprodtest --pyprodtest-webui
```

By default the server listens only on `127.0.0.1` at port `8765`. The page keeps
reconnecting between runs, so PyProdTest reuses an existing browser tab instead
of opening a new one. Use `--pyprodtest-webui-host` and
`--pyprodtest-webui-port` to expose a different endpoint; port `0` selects a
free port but cannot reuse a tab between runs.

## Test order

PyProdTest runs and displays tests in pytest's final collection order. Tests in
one module are normally collected in definition order. For a production plan
that spans modules, put an explicit node-ID order in the project's
`conftest.py`:

```python
TEST_PLAN = (
    "test/test_integration.py::test_one",
    "test/test_integration.py::test_inputs",
    "test/test_integration.py::test_two",
)


def pytest_collection_modifyitems(items):
    """Put planned tests first and retain collection order for everything else."""
    planned_position = {nodeid: index for index, nodeid in enumerate(TEST_PLAN)}
    fallback = len(TEST_PLAN)
    items.sort(key=lambda item: planned_position.get(item.nodeid, fallback))
```

This uses pytest's supported collection hook, so execution order, the live UI,
and report observers all see the same plan. Node IDs can be inspected with
`uv run pytest --collect-only -q`.

PyProdTest also streams `INFO` and higher log messages to the terminal during a
run. Users can still select another threshold with pytest's
`--log-cli-level=LEVEL` option.
