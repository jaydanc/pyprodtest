"""Load and validate project configuration from pyprodtest.yaml."""

from dataclasses import dataclass, field
from pathlib import Path

import pytest
import yaml

DEFAULT_UI_NAME = "Production test execution"


@dataclass(frozen=True)
class UiConfig:
    """Configuration for the live operator UI."""

    enabled: bool = True
    host: str = "127.0.0.1"
    port: int = 8765


@dataclass(frozen=True)
class ReportsConfig:
    """Configuration shared by the final report observers."""

    output: str = "pyprodtest-report"
    html: bool = True
    json: bool = True
    csv: bool = True
    pdf: bool = True


@dataclass(frozen=True)
class PyProdTestConfig:
    """Validated settings for one PyProdTest session."""

    name: str = DEFAULT_UI_NAME
    tests: list[str] | None = None
    ui: UiConfig = field(default_factory=UiConfig)
    reports: ReportsConfig = field(default_factory=ReportsConfig)


def load_config(rootpath: Path) -> PyProdTestConfig:
    """Load pyprodtest.yaml from the pytest project root."""
    config_path = rootpath / "pyprodtest.yaml"
    if not config_path.exists():
        return PyProdTestConfig()

    try:
        document = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as error:
        raise pytest.UsageError(
            f"Invalid PyProdTest configuration {config_path}: {error}"
        ) from error
    if not isinstance(document, dict):
        raise pytest.UsageError(
            f"PyProdTest configuration {config_path} must contain a YAML mapping"
        )

    name = _non_empty_string(document.get("name", DEFAULT_UI_NAME), "name")
    tests = _load_tests(document.get("tests"))
    ui = _mapping(document.get("ui", {}), "ui")
    reports = _mapping(document.get("reports", {}), "reports")
    return PyProdTestConfig(
        name=name,
        tests=tests,
        ui=UiConfig(
            enabled=_boolean(ui.get("enabled", True), "ui.enabled"),
            host=_non_empty_string(ui.get("host", "127.0.0.1"), "ui.host"),
            port=_port(ui.get("port", 8765)),
        ),
        reports=ReportsConfig(
            output=_non_empty_string(
                reports.get("output", "pyprodtest-report"), "reports.output"
            ),
            html=_boolean(reports.get("html", True), "reports.html"),
            json=_boolean(reports.get("json", True), "reports.json"),
            csv=_boolean(reports.get("csv", True), "reports.csv"),
            pdf=_boolean(reports.get("pdf", True), "reports.pdf"),
        ),
    )


def apply_test_plan(
    config: pytest.Config, items: list[pytest.Item], plan: list[str] | None
) -> None:
    """Select and order collected items using the configured test plan."""
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


def _load_tests(value: object) -> list[str] | None:
    if value is None:
        return None
    if not isinstance(value, list) or not all(
        isinstance(selection, str) and selection for selection in value
    ):
        raise pytest.UsageError(
            "PyProdTest configuration 'tests' must be a list of paths or node IDs"
        )
    return [selection.replace("\\", "/") for selection in value]


def _mapping(value: object, setting: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise pytest.UsageError(
            f"PyProdTest configuration '{setting}' must be a mapping"
        )
    return value


def _boolean(value: object, setting: str) -> bool:
    if not isinstance(value, bool):
        raise pytest.UsageError(
            f"PyProdTest configuration '{setting}' must be true or false"
        )
    return value


def _non_empty_string(value: object, setting: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise pytest.UsageError(
            f"PyProdTest configuration '{setting}' must be a non-empty string"
        )
    return value.strip()


def _port(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 65535:
        raise pytest.UsageError(
            "PyProdTest configuration 'ui.port' must be an integer from 0 to 65535"
        )
    return value


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
