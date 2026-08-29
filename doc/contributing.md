# Contributing

PyProdTest uses Python 3.13+, a `src/` layout, and a locked uv environment.

## Set up the repository

```powershell
git clone https://github.com/jaydanc/pyprodtest.git
cd pyprodtest
uv sync --all-groups
```

## Run checks

```powershell
uv run ruff format --check .
uv run ruff check .
uv run pytest -p pyprodtest
```

The explicit plugin flag ensures the repository's plugin is loaded during local
tests.

## Preview the documentation

```powershell
uv run mkdocs serve
```

Open `http://127.0.0.1:8000`. Validate a production build with:

```powershell
uv run mkdocs build --strict
```

## Project boundaries

- `src/pyprodtest/` is the supported public API.
- `src/_pyprodtest/` contains private pytest integration and observers.
- `test/` contains behavior and integration tests.
- `doc/design.md` records the observer/input-acceptor architecture and diagram
  update backlog.
