import logging
from types import SimpleNamespace

from _pyprodtest import hooks
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
