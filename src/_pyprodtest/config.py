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


@dataclass
class ReportsConfig:
    """Configuration shared by the final report observers."""

    output: str | Path = "pyprodtest-report"
    html: bool = True
    json: bool = True
    csv: bool = True
    pdf: bool = True
    enabled: bool = True
    dut_id: str | None = None

    @property
    def output_path(self) -> Path:
        """Return the extensionless report directory and name as one path."""
        return Path(self.output)

    @property
    def path(self) -> Path:
        """Return the report output directory."""
        return self.output_path.parent

    @path.setter
    def path(self, value: str | Path) -> None:
        self.output = Path(value) / self.name

    @property
    def name(self) -> str:
        """Return the extensionless report base name."""
        return self.output_path.name

    @name.setter
    def name(self, value: str | Path) -> None:
        self.output = self.path / Path(value)


@dataclass(frozen=True)
class PyProdTestConfig:
    """Validated settings for one PyProdTest session."""

    name: str = DEFAULT_UI_NAME
    loop: bool = False
    test_order: list[str] | None = None
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
    test_order = _load_test_order(document.get("test_order"))
    ui = _mapping(document.get("ui", {}), "ui")
    reports = _mapping(document.get("reports", {}), "reports")
    return PyProdTestConfig(
        name=name,
        loop=_boolean(document.get("loop", False), "loop"),
        test_order=test_order,
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


def apply_test_order(items: list[pytest.Item], test_order: list[str] | None) -> None:
    """Order collected items using the configured filename-based order."""
    if test_order is None:
        return

    ranked = [
        (_selection_index(item, test_order), position, item)
        for position, item in enumerate(items)
    ]
    ranked.sort(key=lambda entry: (entry[0], entry[1]))
    items[:] = [item for _, _, item in ranked]


def _load_test_order(value: object) -> list[str] | None:
    if value is None:
        return None
    if not isinstance(value, list) or not all(
        isinstance(selection, str) and selection for selection in value
    ):
        raise pytest.UsageError(
            "PyProdTest configuration 'test_order' must be a list of filenames"
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


def _selection_index(item: pytest.Item, test_order: list[str]) -> int:
    return next(
        (
            index
            for index, selection in enumerate(test_order)
            if _matches(item, selection)
        ),
        len(test_order),
    )


def _matches(item: pytest.Item, selection: str) -> bool:
    selection_path, separator, selection_name = selection.partition("::")
    if Path(selection_path).name != Path(item.path).name:
        return False
    if not separator:
        return True

    _, _, item_name = item.nodeid.partition("::")
    return item_name == selection_name or item_name.startswith(f"{selection_name}[")
