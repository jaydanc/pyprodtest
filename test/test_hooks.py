import logging
from pathlib import Path
from types import SimpleNamespace

import pytest

from _pyprodtest import hooks
from _pyprodtest.config import (
    DEFAULT_UI_NAME,
    PyProdTestConfig,
    ReportsConfig,
    apply_test_order,
    load_config,
)
from _pyprodtest.observers import JsonObserver
from _pyprodtest.test_record import CapturedLog, MeasurementSeries, TestRecord


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


def test_yaml_test_order_orders_matching_filenames_and_leaves_the_rest(tmp_path: Path):
    (tmp_path / "pyprodtest.yaml").write_text(
        "test_order:\n  - test_device.py\n  - missing_test.py\n  - test_hooks.py::test_second\n",
        encoding="utf-8",
    )
    items = [
        SimpleNamespace(
            path=tmp_path / "test" / "test_hooks.py",
            nodeid="test/test_hooks.py::test_first",
        ),
        SimpleNamespace(
            path=tmp_path / "integration" / "test_device.py",
            nodeid="test/integration/test_device.py::test_input",
        ),
        SimpleNamespace(
            path=tmp_path / "test" / "test_hooks.py",
            nodeid="test/test_hooks.py::test_second",
        ),
        SimpleNamespace(
            path=tmp_path / "test" / "test_other.py",
            nodeid="test/test_other.py::test_output",
        ),
    ]

    apply_test_order(items, load_config(tmp_path).test_order)

    assert [item.nodeid for item in items] == [
        "test/integration/test_device.py::test_input",
        "test/test_hooks.py::test_second",
        "test/test_hooks.py::test_first",
        "test/test_other.py::test_output",
    ]


def test_yaml_configures_name_ui_and_report_formats(tmp_path: Path):
    (tmp_path / "pyprodtest.yaml").write_text(
        """name: Device acceptance
loop: true
ui:
  enabled: false
  host: 0.0.0.0
  port: 9000
reports:
  output: reports/device
  html: true
  json: false
  csv: false
  pdf: true
test_order:
  - test/device_test.py
""",
        encoding="utf-8",
    )

    config = load_config(tmp_path)

    assert config.name == "Device acceptance"
    assert config.loop is True
    assert config.ui.enabled is False
    assert config.ui.host == "0.0.0.0"
    assert config.ui.port == 9000
    assert config.reports.output == "reports/device"
    assert config.reports.html is True
    assert config.reports.json is False
    assert config.reports.csv is False
    assert config.reports.pdf is True


def test_ui_title_has_default_without_yaml(tmp_path: Path):
    config = load_config(tmp_path)

    assert config.name == DEFAULT_UI_NAME
    assert config.loop is False
    assert config.test_order is None
    assert config.ui.enabled is True
    assert config.reports.html is True
    assert config.reports.json is True
    assert config.reports.csv is True
    assert config.reports.pdf is True


def test_loop_config_must_be_boolean(tmp_path: Path):
    (tmp_path / "pyprodtest.yaml").write_text("loop: forever\n", encoding="utf-8")

    with pytest.raises(pytest.UsageError, match="'loop' must be true or false"):
        load_config(tmp_path)


def test_only_enabled_report_observers_are_composed():
    config = PyProdTestConfig(
        reports=ReportsConfig(html=False, json=True, csv=False, pdf=False)
    )

    observers = hooks._create_report_observers(config)

    assert len(observers) == 1
    assert isinstance(observers[0], JsonObserver)


def test_loop_iteration_resets_records_and_runs_items_once():
    events = []
    calls = []
    state = hooks.PluginState(
        records={
            "test_a": TestRecord(
                name="A",
                nodeid="test_a",
                outcome="failed",
                duration=1.2,
                failure_reason="old failure",
                logs=[CapturedLog("now", "INFO", "test", "old")],
                measurements=[MeasurementSeries("voltage", "time")],
            ),
            "test_b": TestRecord(name="B", nodeid="test_b", outcome="passed"),
        },
        observers=[
            SimpleNamespace(
                on_loop_tests_start=lambda run_index: events.append(
                    ("start", run_index)
                ),
                on_loop_tests_finished=lambda run_index: events.append(
                    ("finished", run_index)
                ),
            )
        ],
    )
    state.config.reports.dut_id = "SN-1234"

    class Hook:
        def pytest_runtest_protocol(self, item, nextitem):
            calls.append((item.nodeid, nextitem.nodeid if nextitem else None))
            state.records[item.nodeid].outcome = "passed"

    hook = Hook()
    items = [
        SimpleNamespace(nodeid="test_a", config=SimpleNamespace(hook=hook)),
        SimpleNamespace(nodeid="test_b", config=SimpleNamespace(hook=hook)),
    ]
    session = SimpleNamespace(
        items=items,
        shouldfail=None,
        shouldstop=None,
        Failed=RuntimeError,
        Interrupted=RuntimeError,
    )

    hooks._run_loop_iteration(session, 3, state)

    assert events == [("start", 3), ("finished", 3)]
    assert calls == [("test_a", "test_b"), ("test_b", None)]
    assert state.config.reports.dut_id is None
    assert state.current_test_nodeid is None
    assert state.records["test_a"].outcome == "passed"
    assert state.records["test_a"].duration == 0.0
    assert state.records["test_a"].failure_reason == ""
    assert state.records["test_a"].logs == []
    assert state.records["test_a"].measurements == []


def test_loop_iteration_tears_down_session_state_before_notifying_observers():
    events = []

    class SetupState:
        def teardown_exact(self, nextitem):
            assert nextitem is None
            events.append("teardown")

    state = hooks.PluginState(
        records={"test_a": TestRecord(name="A", nodeid="test_a")},
        observers=[
            SimpleNamespace(
                on_loop_tests_start=lambda run_index: events.append("start"),
                on_loop_tests_finished=lambda run_index: events.append("finished"),
            )
        ],
    )

    class Hook:
        def pytest_runtest_protocol(self, item, nextitem):
            events.append("test")

    item = SimpleNamespace(
        nodeid="test_a",
        config=SimpleNamespace(hook=Hook()),
    )
    session = SimpleNamespace(
        items=[item],
        shouldfail=None,
        shouldstop=None,
        Failed=RuntimeError,
        Interrupted=RuntimeError,
        _setupstate=SetupState(),
    )

    hooks._run_loop_iteration(session, 1, state)

    assert events == ["start", "test", "teardown", "finished"]
