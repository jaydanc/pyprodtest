# PyProdTest

PyProdTest is an early-stage pytest plugin for running production tests. It adds
test metadata, operator prompts, a live browser view, ordered test plans, and
HTML, JSON, CSV, and PDF reports.

Read the [documentation](https://jaydanc.github.io/pyprodtest/)

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
