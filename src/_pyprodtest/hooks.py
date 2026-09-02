"""Pytest plugin hooks for capturing and forwarding test information."""

import logging
from collections.abc import Iterable
from dataclasses import dataclass, field

import pytest

from _pyprodtest.config import PyProdTestConfig, apply_test_order, load_config
from _pyprodtest.fixtures import dut as dut
from _pyprodtest.fixtures import input as input
from _pyprodtest.fixtures import measure as measure
from _pyprodtest.fixtures import report as report
from _pyprodtest.input_acceptors import ConsoleInputAcceptor, InputAcceptor
from _pyprodtest.observers import (
    CsvObserver,
    HtmlObserver,
    JsonObserver,
    PdfObserver,
    TestObserver,
)
from _pyprodtest.observers.web_ui.observer import WebObserver
from _pyprodtest.test_record import CapturedLog, TestRecord

LOGGER = logging.getLogger(__name__)


@dataclass
class PluginState:
    """State owned by one pytest session."""

    observers: list[TestObserver] = field(default_factory=list)
    records: dict[str, TestRecord] = field(default_factory=dict)
    current_test_nodeid: str | None = None
    log_handler: logging.Handler | None = None
    input_acceptor: InputAcceptor = field(default_factory=ConsoleInputAcceptor)
    config: PyProdTestConfig = field(default_factory=PyProdTestConfig)

    def on_tests_start(self) -> None:
        for observer in self.observers:
            observer.on_tests_start()

    def on_tests_collected(self, test_records: list[TestRecord]) -> None:
        for observer in self.observers:
            observer.on_tests_collected(test_records)

    def on_loop_tests_start(self, run_index: int) -> None:
        for observer in self.observers:
            observer.on_loop_tests_start(run_index)

    def on_loop_tests_finished(self, run_index: int) -> None:
        for observer in self.observers:
            observer.on_loop_tests_finished(run_index)

    def on_test_run(self, test_record: TestRecord) -> None:
        for observer in self.observers:
            observer.on_test_run(test_record)

    def on_test_end(self, test_record: TestRecord) -> None:
        for observer in self.observers:
            observer.on_test_end(test_record)

    def on_tests_finished(self) -> None:
        for observer in self.observers:
            observer.on_tests_finished()


class TestLogHandler(logging.Handler):
    """Attach log records to the currently executing test."""

    def emit(self, record: logging.LogRecord) -> None:
        if _state is None or _state.current_test_nodeid is None:
            return

        test_record = _state.records.get(_state.current_test_nodeid)
        if test_record is not None:
            test_record.logs.append(CapturedLog.from_record(record))


_state: PluginState | None = None


def get_plugin_state() -> PluginState:
    """Return the active PyProdTest plugin state."""
    if _state is None:
        raise RuntimeError("PyProdTest is not configured")
    return _state


def pytest_configure(config: pytest.Config) -> None:
    """Create isolated plugin state for this pytest session."""
    global _state

    _enable_live_logging(config)

    project_config = load_config(config.rootpath)

    collect_only = config.getoption("--collect-only")
    observers = _create_report_observers(project_config)
    input_acceptor: InputAcceptor = ConsoleInputAcceptor()
    if project_config.ui.enabled and not collect_only:
        web_observer = WebObserver(
            host=project_config.ui.host,
            port=project_config.ui.port,
            name=project_config.name,
            open_browser=True,
            reports=project_config.reports,
        )
        observers.append(web_observer)
        input_acceptor = web_observer.input_acceptor

    root_logger = logging.getLogger()
    handler = TestLogHandler()
    root_logger.addHandler(handler)
    if not root_logger.isEnabledFor(logging.INFO):
        root_logger.setLevel(logging.INFO)

    _state = PluginState(
        observers=observers,
        log_handler=handler,
        input_acceptor=input_acceptor,
        config=project_config,
    )
    LOGGER.debug("PyProdTest observers configured: %s", observers)


def pytest_unconfigure() -> None:
    """Release state after the pytest session."""
    global _state
    if _state is not None and _state.log_handler is not None:
        root_logger = logging.getLogger()
        root_logger.removeHandler(_state.log_handler)
    _state = None


def pytest_sessionstart(session: pytest.Session) -> None:
    """Notify observers that pytest is about to run tests."""
    if _state is not None:
        _state.on_tests_start()


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Notify observers that pytest has finished running tests."""
    if _state is not None and not session.config.getoption("--collect-only"):
        _state.on_tests_finished()


def pytest_runtestloop(session: pytest.Session) -> bool | None:
    """Optionally repeat the collected test sequence until pytest stops."""
    if _state is None or not _state.config.loop:
        return None

    if session.testsfailed and not session.config.option.continue_on_collection_errors:
        raise session.Interrupted(
            f"{session.testsfailed} error{'s' if session.testsfailed != 1 else ''} during collection"
        )

    if session.config.option.collectonly:
        return True

    if not session.items:
        return True

    run_index = 1
    while True:
        _run_loop_iteration(session, run_index, _state)
        run_index += 1


def pytest_report_collectionfinish(items: list[pytest.Item]) -> None:
    """Build records and notify observers after collection."""
    if _state is None:
        return

    for item in items:
        test_metadata = getattr(getattr(item, "function", None), "test_meta", {})
        _state.records[item.nodeid] = TestRecord(
            name=test_metadata.get("name", item.nodeid),
            description=test_metadata.get("desc", ""),
            requirements=list(test_metadata.get("requirements", [])),
            steps=list(test_metadata.get("steps", [])),
            nodeid=item.nodeid,
        )

    records = list(_state.records.values())
    LOGGER.debug("Collected test records: %s", records)
    _state.on_tests_collected(records)


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Apply optional user-facing test ordering to pytest's collected items."""
    if _state is not None:
        apply_test_order(items, _state.config.test_order)


def pytest_runtest_call(item: pytest.Item) -> None:
    """Notify observers immediately before the test body runs."""
    if _state is None or (test_record := _state.records.get(item.nodeid)) is None:
        return

    test_record.outcome = "running"
    _state.on_test_run(test_record)


def pytest_runtest_logstart(nodeid: str, location: tuple[str, int | None, str]) -> None:
    """Begin attributing log records to a test."""
    if _state is not None:
        _state.current_test_nodeid = nodeid


def pytest_runtest_logfinish(
    nodeid: str, location: tuple[str, int | None, str]
) -> None:
    """Stop attributing log records after a test finishes."""
    if _state is not None and _state.current_test_nodeid == nodeid:
        _state.current_test_nodeid = None


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    """Capture phase results and notify observers after teardown."""
    if _state is None or (test_record := _state.records.get(report.nodeid)) is None:
        return

    _update_test_record(test_record, report)

    if report.when == "teardown":
        _state.on_test_end(test_record)


def _update_test_record(test_record: TestRecord, report: pytest.TestReport) -> None:
    """Apply one pytest phase report to a domain test record."""
    test_record.duration += report.duration
    if report.failed:
        test_record.outcome = "failed"
        failure_reason = report.longreprtext or str(report.longrepr)
        if test_record.failure_reason:
            test_record.failure_reason += f"\n\n{failure_reason}"
        else:
            test_record.failure_reason = failure_reason
    elif report.when == "call" and test_record.outcome != "failed":
        test_record.outcome = report.outcome
    elif report.skipped and test_record.outcome not in {"failed", "passed"}:
        test_record.outcome = "skipped"


def _run_loop_iteration(
    session: pytest.Session, run_index: int, state: PluginState
) -> None:
    """Run the collected item list once and publish loop-run lifecycle events."""
    _reset_test_records(state.records.values())
    state.config.reports.dut_id = None
    state.current_test_nodeid = None
    state.on_loop_tests_start(run_index)

    try:
        for index, item in enumerate(session.items):
            nextitem = (
                session.items[index + 1] if index + 1 < len(session.items) else None
            )
            item.config.hook.pytest_runtest_protocol(item=item, nextitem=nextitem)
            if session.shouldfail:
                raise session.Failed(session.shouldfail)
            if session.shouldstop:
                raise session.Interrupted(session.shouldstop)
    finally:
        _teardown_remaining_session_state(session)

    state.on_loop_tests_finished(run_index)


def _reset_test_records(test_records: Iterable[TestRecord]) -> None:
    """Clear runtime fields while preserving collected metadata."""
    for test_record in test_records:
        test_record.outcome = "pending"
        test_record.duration = 0.0
        test_record.failure_reason = ""
        test_record.logs.clear()
        test_record.measurements.clear()


def _teardown_remaining_session_state(session: pytest.Session) -> None:
    """Ensure session-scoped fixture finalizers run before the next loop pass."""
    setup_state = getattr(session, "_setupstate", None)
    if setup_state is not None:
        setup_state.teardown_exact(None)


def _create_report_observers(
    project_config: PyProdTestConfig,
) -> list[TestObserver]:
    """Compose only the report observers enabled for this session."""
    observers: list[TestObserver] = []
    reports = project_config.reports

    if reports.html:
        observers.append(HtmlObserver(reports))

    if reports.json:
        observers.append(JsonObserver(reports))

    if reports.csv:
        observers.append(CsvObserver(reports))

    if reports.pdf:
        observers.append(PdfObserver(reports))

    return observers


def _enable_live_logging(config: pytest.Config) -> None:
    """Show INFO logs live unless the user configured another CLI level."""
    if config.getoption("--log-cli-level") is not None:
        return

    config.option.log_cli_level = config.getini("log_cli_level") or "INFO"
