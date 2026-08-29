"""Load and apply user-facing YAML production test plans."""

from pathlib import Path

import pytest
import yaml


def apply_test_plan(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Select and order collected items using the configured test plan."""
    plan = _load_plan(config)
    if plan is None:
        return

    ranked = [(item, _selection_index(item.nodeid, plan)) for item in items]
    matched = {plan[index] for _, index in ranked if index < len(plan)}
    unmatched = [selection for selection in plan if selection not in matched]
    if unmatched:
        formatted = "\n  - ".join(unmatched)
        raise pytest.UsageError(
            f"PyProdTest plan entries matched no tests:\n  - {formatted}"
        )

    ranked.sort(key=lambda entry: entry[1])
    selected = [item for item, index in ranked if index < len(plan)]
    deselected = [item for item, index in ranked if index == len(plan)]
    items[:] = selected
    if deselected:
        config.hook.pytest_deselected(items=deselected)


def _selection_index(nodeid: str, plan: list[str]) -> int:
    return next(
        (index for index, selection in enumerate(plan) if _matches(nodeid, selection)),
        len(plan),
    )


def _matches(nodeid: str, selection: str) -> bool:
    return (
        nodeid == selection
        or nodeid.startswith(f"{selection}::")
        or nodeid.startswith(f"{selection}[")
    )


def _load_plan(config: pytest.Config) -> list[str] | None:
    if config.getoption("--pyprodtest-ignore-plan"):
        return None

    configured_path = config.getoption("--pyprodtest-plan")
    plan_path = Path(configured_path or "pyprodtest.yaml")
    if not plan_path.is_absolute():
        plan_path = config.rootpath / plan_path
    if not plan_path.exists():
        if configured_path:
            raise pytest.UsageError(f"PyProdTest plan does not exist: {plan_path}")
        return None

    try:
        document = yaml.safe_load(plan_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as error:
        raise pytest.UsageError(
            f"Invalid PyProdTest plan {plan_path}: {error}"
        ) from error

    selections = document.get("tests") if isinstance(document, dict) else None
    if not isinstance(selections, list) or not all(
        isinstance(selection, str) and selection for selection in selections
    ):
        raise pytest.UsageError(
            f"PyProdTest plan {plan_path} must contain a 'tests' list of paths or node IDs"
        )
    return [selection.replace("\\", "/") for selection in selections]
