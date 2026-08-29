from pathlib import Path

import pytest

from _pyprodtest.observers import HtmlObserver, TestObserver
from _pyprodtest.observers.html_report import ReportSettings
from _pyprodtest.test_record import CapturedLog, TestRecord


def test_observer_is_an_interface():
    with pytest.raises(TypeError):
        TestObserver()


def test_html_observer_reports_lifecycle_and_escapes_content(tmp_path: Path):
    report_path = tmp_path / "reports" / "tests.html"
    record = TestRecord(
        name="A <test>",
        description="Uses an & safely",
        requirements=["REQ-1"],
        steps=["Start", "Finish"],
        logs=[
            CapturedLog(
                timestamp="2026-08-29T12:34:56.789+01:00",
                level="INFO",
                logger="test.instrument",
                message="Measured <5V> & stable",
            )
        ],
    )
    settings = ReportSettings.from_output_path(report_path)
    observer = HtmlObserver(settings)

    observer.on_tests_collected([record])
    assert not report_path.exists()

    record.outcome = "running"
    observer.on_test_run(record)
    assert not report_path.exists()

    record.outcome = "passed"
    record.duration = 0.125
    record.failure_reason = "Expected <one>, got &two"
    observer.on_test_end(record)
    settings.path = tmp_path / "final"
    settings.name = "renamed.html"
    observer.finalize()
    report_path = tmp_path / "final" / "renamed.html"
    report = report_path.read_text(encoding="utf-8")

    assert "A &lt;test&gt;" in report
    assert "Uses an &amp; safely" in report
    assert "REQ-1" in report
    assert "Start" in report
    assert "Finish" in report
    assert "Logs (1)" in report
    assert "Failure details" in report
    assert "--pico-font-family" in report
    assert "passed" in report
    assert "2026-08-29T12:34:56.789+01:00" in report
    assert "INFO" in report
    assert "test.instrument" in report
    assert "Measured &lt;5V&gt; &amp; stable" in report
    assert "Expected &lt;one&gt;, got &amp;two" in report
    assert "0.125s" in report


def test_html_observer_can_be_disabled_by_report_settings(tmp_path: Path):
    settings = ReportSettings(path=tmp_path, enabled=False)
    observer = HtmlObserver(settings)
    observer.on_tests_collected([TestRecord(name="Test")])

    observer.finalize()

    assert not settings.output_path.exists()
