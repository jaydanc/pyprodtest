"""Pytest plugin hooks for capturing and forwarding test information."""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field

import pytest

from _pyprodtest.input_acceptors import ConsoleInputAcceptor, InputAcceptor, TestInput
from _pyprodtest.observers import HtmlObserver, TestObserver
from _pyprodtest.observers.html_report import ReportSettings
from _pyprodtest.observers.web_ui import WebUi
from _pyprodtest.test_plan import apply_test_plan
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
    report_settings: ReportSettings = field(default_factory=ReportSettings)
    cleanup_callbacks: list[Callable[[], None]] = field(default_factory=list)

    def on_tests_collected(self, test_records: list[TestRecord]) -> None:
        for observer in self.observers:
            observer.on_tests_collected(test_records)

    def on_test_run(self, test_record: TestRecord) -> None:
        for observer in self.observers:
            observer.on_test_run(test_record)

    def on_test_end(self, test_record: TestRecord) -> None:
        for observer in self.observers:
            observer.on_test_end(test_record)


_state: PluginState | None = None


@pytest.fixture(scope="session")
def report() -> ReportSettings:
    """Return mutable settings for the final standalone HTML report."""
    if _state is None:
        raise RuntimeError("PyProdTest is not configured")
    return _state.report_settings


@pytest.fixture(scope="session")
def input(request: pytest.FixtureRequest) -> TestInput:
    """Return input from the acceptor selected by the plugin's run mode."""
    if _state is None:
        raise RuntimeError("PyProdTest is not configured")

    def accept(prompt: str, input_type: type[str] | type[bool] = str) -> str | bool:
        capture_manager = request.config.pluginmanager.get_plugin("capturemanager")
        if capture_manager is None:
            return _state.input_acceptor.accept(prompt, input_type)

        # pytest's standard disabled-capture context leaves stdin blocked.
        # Explicitly include stdin while suspending capture for the prompt.
        capture_manager.suspend(in_=True)
        try:
            return _state.input_acceptor.accept(prompt, input_type)
        finally:
            capture_manager.resume()

    return accept


class TestLogHandler(logging.Handler):
    """Attach log records to the currently executing test."""

    def emit(self, record: logging.LogRecord) -> None:
        if _state is None or _state.current_test_nodeid is None:
            return

        test_record = _state.records.get(_state.current_test_nodeid)
        if test_record is not None:
            test_record.logs.append(CapturedLog.from_record(record))


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register PyProdTest command-line options."""
    group = parser.getgroup("pyprodtest")
    group.addoption(
        "--pyprodtest-html",
        default="pyprodtest-report.html",
        help="Set the final HTML report output path.",
    )
    group.addoption(
        "--pyprodtest-webui",
        action="store_true",
        dest="pyprodtest_webui",
        default=True,
        help="Open the live operator web UI (enabled by default).",
    )
    group.addoption(
        "--no-pyprodtest-webui",
        action="store_false",
        dest="pyprodtest_webui",
        default=True,
        help="Disable the live operator web UI.",
    )
    group.addoption(
        "--pyprodtest-webui-host",
        default="127.0.0.1",
        help="Host for the live web UI (default: 127.0.0.1).",
    )
    group.addoption(
        "--pyprodtest-webui-port",
        default=8765,
        type=int,
        help="Port for the live web UI; 0 selects a free port (default: 8765).",
    )
    group.addoption(
        "--pyprodtest-plan",
        metavar="PATH",
        help="Select and order tests using a YAML plan (default: pyprodtest.yaml).",
    )
    group.addoption(
        "--pyprodtest-ignore-plan",
        action="store_true",
        help="Ignore pyprodtest.yaml and use normal pytest collection.",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Create isolated plugin state for this pytest session."""
    global _state

    _enable_live_logging(config)

    html_path = config.getoption("--pyprodtest-html")
    report_settings = ReportSettings.from_output_path(html_path)
    html_observer = HtmlObserver(report_settings)
    observers: list[TestObserver] = [html_observer]

    cleanup_callbacks: list[Callable[[], None]] = [html_observer.finalize]
    input_acceptor: InputAcceptor = ConsoleInputAcceptor()
    if config.getoption("pyprodtest_webui"):
        web_ui = WebUi(
            host=config.getoption("--pyprodtest-webui-host"),
            port=config.getoption("--pyprodtest-webui-port"),
        )
        web_ui.start(open_browser=True)
        LOGGER.info("PyProdTest web UI: %s", web_ui.url)
        observers.append(web_ui.observer)
        input_acceptor = web_ui.input_acceptor
        cleanup_callbacks.append(web_ui.finish_and_stop)

    root_logger = logging.getLogger()
    handler = TestLogHandler()
    root_logger.addHandler(handler)
    if not root_logger.isEnabledFor(logging.INFO):
        root_logger.setLevel(logging.INFO)

    _state = PluginState(
        observers=observers,
        log_handler=handler,
        input_acceptor=input_acceptor,
        report_settings=report_settings,
        cleanup_callbacks=cleanup_callbacks,
    )
    LOGGER.debug("PyProdTest observers configured: %s", observers)


def _enable_live_logging(config: pytest.Config) -> None:
    """Show INFO logs live unless the user configured another CLI level."""
    if config.getoption("--log-cli-level") is not None:
        return

    config.option.log_cli_level = config.getini("log_cli_level") or "INFO"


def pytest_unconfigure() -> None:
    """Release state after the pytest session."""
    global _state
    if _state is not None and _state.log_handler is not None:
        root_logger = logging.getLogger()
        root_logger.removeHandler(_state.log_handler)
    if _state is not None:
        for cleanup in _state.cleanup_callbacks:
            cleanup()
    _state = None


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
    """Apply an optional user-facing test plan to pytest's collected items."""
    apply_test_plan(config, items)


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
