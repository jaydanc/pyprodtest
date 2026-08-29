# In Progress

[See prototype here](https://github.com/jaydanc/pyprodtest/tree/prototype)

[See architecture here](/doc/design.md)

## Build Guide:

uv pip install -e .
uv run ruff format --check .
uv run ruff check .
uv run pytest -p pyprodtest
