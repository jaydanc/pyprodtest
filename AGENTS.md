# AGENTS.md

## Project overview

PyProdTest is an early-stage pytest plugin for capturing production-test metadata and results. It targets Python 3.13+, uses `uv`, and follows a `src/` package layout.

- `src/pyprodtest/` is the small, stable public API.
- `src/_pyprodtest/` contains plugin internals and pytest hook implementations.
- `test/` contains pytest integration tests.
- `doc/design.md` describes the intended observer/provider architecture.

Read `README.md`, `pyproject.toml`, and `doc/design.md` before making architectural changes.

## Setup and verification

Use the locked `uv` environment; do not introduce another environment or dependency manager.

```powershell
uv sync
uv run ruff format --check .
uv run ruff check .
uv run pytest -p pyprodtest
```

The explicit `-p pyprodtest` matters because it loads the package's pytest entry point during local tests. Run the full suite after changes to decorators, hooks, records, packaging, or plugin registration. Add focused tests for new behavior and regression tests for bug fixes.

If the execution sandbox prevents `uv` from using its user cache, point it at a disposable workspace-local directory for that command (for example, set `UV_CACHE_DIR` to `.uv-cache`). Do not commit that cache.

## Architecture and API rules

- Keep the public surface in `src/pyprodtest/__init__.py` intentionally small. Re-export supported user-facing APIs there and update `__all__` deliberately.
- Treat modules under `src/_pyprodtest/` as private implementation details. Tests and examples should import from `pyprodtest` unless they specifically test internals.
- Preserve separation between the core, test observers, and input providers described in `doc/design.md`. Avoid coupling pytest hooks directly to a particular future UI, report generator, or input provider.
- Take extra care when changing data models or interfaces: prefer explicit fields, backward-compatible evolution, and tests that cover every consumer.
- Keep pytest hook signatures compatible with the supported pytest version. Do not rename hooks or alter their parameters without checking pytest's hook specification.
- Avoid mutable module-level state where practical. When plugin state must span hooks, ensure it is initialized and cleared per pytest session so repeated/in-process test runs do not leak state or duplicate logging handlers.

## Python conventions

- Support the Python version declared by `requires-python` and `.python-version`; do not add compatibility shims for older versions unless the project metadata changes.
- Prefer explicit imports in production code and tests. Do not add new wildcard imports.
- Add type hints to new or substantially changed functions and data structures. Prefer standard-library types and simple data models over unnecessary dependencies.
- Use clear docstrings for public APIs and pytest hooks where intent is not obvious. Comments should explain why, not restate the code.
- Format Python with `uv run ruff format .` and lint it with `uv run ruff check .`. Keep Ruff configuration in `pyproject.toml` and avoid unrelated whole-repository churn.
- Use `logging` rather than `print` for plugin diagnostics. Do not change the root logger's handlers or level without restoring prior state; prefer plugin-scoped logging.

## Testing guidance

- Test behavior visible to plugin users: decorator combinations, metadata defaults, collection, setup/call/teardown reporting, logging capture, and terminal summaries.
- Include tests for multiple decorated tests and repeated pytest sessions; these expose shared-state bugs.
- Avoid assertions that depend on incidental ordering unless ordering is part of the contract.
- Keep test fixtures minimal and deterministic. Tests must not require network access, credentials, wall-clock timing, or a particular machine path.
- A passing test suite is required, but do not weaken or delete tests simply to make a change pass.

## Change discipline

- Inspect `git status` and relevant diffs before editing. Preserve user changes and do not modify unrelated files.
- Keep changes narrowly scoped. Do not refactor adjacent code unless it is necessary for correctness or explicitly requested.
- Update documentation when public APIs, setup commands, behavior, or architecture change.
- Do not edit `uv.lock` by hand. Regenerate it with `uv` only when dependency metadata changes, and include both files in the same change.
- Never commit generated artifacts, caches, virtual environments, secrets, or machine-specific paths.
- Do not create commits, branches, tags, or publish packages unless explicitly requested.

## Before handing off

1. Review the diff for accidental or unrelated edits.
2. Run `uv run ruff format --check .`, `uv run ruff check .`, and `uv run pytest -p pyprodtest` (using the sandbox cache workaround only when needed).
3. Report what changed, what was verified, and any remaining limitation or failing test accurately.
