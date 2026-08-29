"""Pytest plugin hooks for capturing and forwarding test information."""

import logging
from dataclasses import dataclass, field

import pytest

from _pyprodtest.observers import HtmlObserver, TestObserver
from _pyprodtest.test_record import TestRecord

LOGGER = logging.getLogger(__name__)


@dataclass
class PluginState:
    """State owned by one pytest session."""

    observers: list[TestObserver] = field(default_factory=list)
    records: dict[str, TestRecord] = field(default_factory=dict)

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


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register PyProdTest command-line options."""
    group = parser.getgroup("pyprodtest")
    group.addoption(
        "--pyprodtest-html",
        metavar="PATH",
        help="Write a live HTML test report to PATH.",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Create isolated plugin state for this pytest session."""
    global _state

    observers: list[TestObserver] = []
    html_path = config.getoption("--pyprodtest-html")
    if html_path:
        observers.append(HtmlObserver(html_path))

    _state = PluginState(observers=observers)
    LOGGER.debug("PyProdTest observers configured: %s", observers)


def pytest_unconfigure() -> None:
    """Release state after the pytest session."""
    global _state
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


def pytest_runtest_call(item: pytest.Item) -> None:
    """Notify observers immediately before the test body runs."""
    if _state is None or (test_record := _state.records.get(item.nodeid)) is None:
        return

    test_record.outcome = "running"
    _state.on_test_run(test_record)


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
        LOGGER.error("Test %s failed:\n%s", report.nodeid, failure_reason)
    elif report.when == "call" and test_record.outcome != "failed":
        test_record.outcome = report.outcome
    elif report.skipped and test_record.outcome not in {"failed", "passed"}:
        test_record.outcome = "skipped"
