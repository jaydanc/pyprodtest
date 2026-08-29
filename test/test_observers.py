from pathlib import Path

import pytest

from _pyprodtest.observers import HtmlObserver, TestObserver
from _pyprodtest.test_record import TestRecord


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
    )
    observer = HtmlObserver(report_path)

    observer.on_tests_collected([record])
    assert "pending" in report_path.read_text(encoding="utf-8")

    record.outcome = "running"
    observer.on_test_run(record)
    assert "running" in report_path.read_text(encoding="utf-8")

    record.outcome = "passed"
    record.duration = 0.125
    observer.on_test_end(record)
    report = report_path.read_text(encoding="utf-8")

    assert "A &lt;test&gt;" in report
    assert "Uses an &amp; safely" in report
    assert "REQ-1" in report
    assert "Start → Finish" in report
    assert "passed" in report
    assert "0.125s" in report
