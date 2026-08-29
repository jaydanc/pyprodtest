import logging
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from _pyprodtest import hooks
from _pyprodtest.config import (
    DEFAULT_UI_NAME,
    PyProdTestConfig,
    ReportsConfig,
    apply_test_plan,
    load_config,
)
from _pyprodtest.observers import JsonObserver
from _pyprodtest.report_settings import ReportSettings
from _pyprodtest.test_record import TestRecord


def test_failed_report_captures_failure_reason():
    record = TestRecord(name="Broken test", nodeid="test_broken")
    report = SimpleNamespace(
        nodeid=record.nodeid,
        duration=0.25,
        failed=True,
        skipped=False,
        when="call",
        outcome="failed",
        longreprtext="AssertionError: expected 1, got 2",
        longrepr=None,
    )

    hooks._update_test_record(record, report)

    assert record.outcome == "failed"
    assert record.failure_reason == "AssertionError: expected 1, got 2"
    assert record.duration == 0.25


def test_captured_log_preserves_timestamp_level_logger_and_message():
    source = logging.LogRecord(
        name="test.instrument",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Reading: %s V",
        args=(5.1,),
        exc_info=None,
    )

    captured = hooks.CapturedLog.from_record(source)

    assert captured.timestamp
    assert captured.level == "INFO"
    assert captured.logger == "test.instrument"
    assert captured.message == "Reading: 5.1 V"


def test_live_logging_defaults_to_info():
    config = SimpleNamespace(
        option=SimpleNamespace(log_cli_level=None),
        getoption=lambda option: None,
        getini=lambda option: "",
    )

    hooks._enable_live_logging(config)

    assert config.option.log_cli_level == "INFO"


def test_live_logging_preserves_explicit_cli_level():
    config = SimpleNamespace(
        option=SimpleNamespace(log_cli_level="DEBUG"),
        getoption=lambda option: "DEBUG",
        getini=lambda option: "",
    )

    hooks._enable_live_logging(config)

    assert config.option.log_cli_level == "DEBUG"


def test_yaml_plan_selects_and_orders_files_and_node_ids(tmp_path: Path):
    (tmp_path / "pyprodtest.yaml").write_text(
        "tests:\n  - test/test_integration.py\n  - test/test_hooks.py::test_second\n",
        encoding="utf-8",
    )
    deselected = []
    config = SimpleNamespace(
        hook=SimpleNamespace(pytest_deselected=lambda items: deselected.extend(items))
    )
    items = [
        SimpleNamespace(nodeid="test/test_hooks.py::test_first"),
        SimpleNamespace(nodeid="test/test_integration.py::test_input"),
        SimpleNamespace(nodeid="test/test_hooks.py::test_second"),
        SimpleNamespace(nodeid="test/test_integration.py::test_output"),
    ]

    apply_test_plan(config, items, load_config(tmp_path).tests)

    assert [item.nodeid for item in items] == [
        "test/test_integration.py::test_input",
        "test/test_integration.py::test_output",
        "test/test_hooks.py::test_second",
    ]
    assert [item.nodeid for item in deselected] == ["test/test_hooks.py::test_first"]


def test_yaml_configures_name_ui_and_report_formats(tmp_path: Path):
    (tmp_path / "pyprodtest.yaml").write_text(
        """name: Device acceptance
ui:
  enabled: false
  host: 0.0.0.0
  port: 9000
reports:
  output: reports/device
  html: true
  json: false
  csv: false
tests:
  - test/device_test.py
""",
        encoding="utf-8",
    )

    config = load_config(tmp_path)

    assert config.name == "Device acceptance"
    assert config.ui.enabled is False
    assert config.ui.host == "0.0.0.0"
    assert config.ui.port == 9000
    assert config.reports.output == "reports/device"
    assert config.reports.html is True
    assert config.reports.json is False
    assert config.reports.csv is False


def test_ui_title_has_default_without_yaml(tmp_path: Path):
    config = load_config(tmp_path)

    assert config.name == DEFAULT_UI_NAME
    assert config.tests is None
    assert config.ui.enabled is True
    assert config.reports.html is True
    assert config.reports.json is True
    assert config.reports.csv is True


def test_only_enabled_report_observers_are_composed():
    config = PyProdTestConfig(reports=ReportsConfig(html=False, json=True, csv=False))

    observers, cleanup_callbacks = hooks._create_report_observers(
        config, ReportSettings(), collect_only=False
    )

    assert len(observers) == 1
    assert isinstance(observers[0], JsonObserver)
    assert cleanup_callbacks == [observers[0].finalize]


def test_report_output_has_session_timestamp_appended():
    timestamp = datetime(2026, 8, 29, 14, 5, 7, tzinfo=timezone.utc)

    output = hooks._timestamped_report_output("reports/device", timestamp)

    assert output == Path("reports/device-20260829-140507")
