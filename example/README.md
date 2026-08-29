# PyProdTest demo

This standalone uv project installs PyProdTest directly from GitHub and runs a
short operator-assisted device check.

```powershell
uv sync
uv run pytest
```

The browser UI opens at `http://127.0.0.1:8765`. Enter a serial number, then
confirm the status light. Reports are written to `reports/`.

The Git dependency was added with:

```powershell
uv add "pyprodtest @ git+https://github.com/jaydanc/pyprodtest.git"
```
