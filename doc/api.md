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

The plugin also registers two fixtures. They are supplied by pytest rather than
imported from `pyprodtest`.

### `input`

```python
value: str = input("Device serial")
accepted: bool = input("Is the indicator green?", bool)
```

Supported types are `str` and `bool`.

### `report`

The session-scoped fixture exposes:

| Attribute | Meaning |
| --- | --- |
| `path` | Output directory |
| `name` | Extensionless report base name |
| `enabled` | Whether any reports are written |

Modules under `_pyprodtest` are private implementation details and may change
without preserving a public compatibility contract.
