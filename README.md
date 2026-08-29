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

PyProdTest also streams `INFO` and higher log messages to the terminal during a
run. Users can still select another threshold with pytest's
`--log-cli-level=LEVEL` option.
