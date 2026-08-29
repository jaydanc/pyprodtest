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
future live web runs.
