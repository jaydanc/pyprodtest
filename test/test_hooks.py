import logging
from types import SimpleNamespace

from _pyprodtest import hooks
from _pyprodtest.test_record import TestRecord


def test_failed_report_captures_and_logs_failure_reason(caplog):
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

    with caplog.at_level(logging.ERROR, logger=hooks.LOGGER.name):
        hooks._update_test_record(record, report)

    assert record.outcome == "failed"
    assert record.failure_reason == "AssertionError: expected 1, got 2"
    assert record.duration == 0.25
    assert "AssertionError: expected 1, got 2" in caplog.text
