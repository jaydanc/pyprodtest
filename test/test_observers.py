import csv
import json
from pathlib import Path

import pytest

from _pyprodtest.observers import (
    CsvObserver,
    HtmlObserver,
    JsonObserver,
    PdfObserver,
    TestObserver,
)
from _pyprodtest.report_settings import ReportSettings
from _pyprodtest.test_record import (
    CapturedLog,
    MeasurementPoint,
    MeasurementSeries,
    TestRecord,
)


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
        measurements=[
            MeasurementSeries(
                name="Voltage <rail>",
                x_axis="time",
                points=[MeasurementPoint(x="2026-08-29T12:34:56.789+01:00", y=5.02)],
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
    assert "Measured data" in report
    assert "Voltage &lt;rail&gt;" in report
    assert "chart.js@4.4.7" in report
    assert "2026-08-29T12:34:56.789+01:00" in report


def test_html_observer_can_be_disabled_by_report_settings(tmp_path: Path):
    settings = ReportSettings(path=tmp_path, enabled=False)
    observer = HtmlObserver(settings)
    observer.on_tests_collected([TestRecord(name="Test")])

    observer.finalize()

    assert not settings.output_path.exists()


def test_json_and_csv_observers_preserve_test_records(tmp_path: Path):
    settings = ReportSettings(path=tmp_path, name="results")
    record = TestRecord(
        name="Device test",
        requirements=["REQ-1"],
        steps=["Measure voltage"],
        outcome="passed",
        duration=0.5,
        logs=[CapturedLog("now", "INFO", "instrument", "Measured 5V")],
        measurements=[
            MeasurementSeries(
                name="Voltage",
                x_axis="time",
                points=[MeasurementPoint("2026-08-29T12:00:00Z", 5.0)],
            ),
            MeasurementSeries(
                name="Calibration",
                x_axis="linear",
                points=[MeasurementPoint(128.0, 2.5)],
            ),
        ],
    )
    observers = [JsonObserver(settings), CsvObserver(settings)]
    for observer in observers:
        observer.on_tests_collected([record])
        observer.finalize()

    json_report = json.loads((tmp_path / "results.json").read_text(encoding="utf-8"))
    assert json_report["summary"] == {"total": 1, "outcomes": {"passed": 1}}
    assert json_report["tests"][0]["logs"][0]["message"] == "Measured 5V"
    assert [series["name"] for series in json_report["tests"][0]["measurements"]] == [
        "Voltage",
        "Calibration",
    ]
    assert json_report["tests"][0]["measurements"][1]["points"] == [
        {"x": 128.0, "y": 2.5}
    ]

    with (tmp_path / "results.csv").open(encoding="utf-8", newline="") as report:
        row = next(csv.DictReader(report))
    assert json.loads(row["requirements"]) == ["REQ-1"]
    assert json.loads(row["steps"]) == ["Measure voltage"]
    assert json.loads(row["logs"])[0]["message"] == "Measured 5V"
    measurements = json.loads(row["measurements"])
    assert [series["name"] for series in measurements] == ["Voltage", "Calibration"]
    assert measurements[0]["points"][0]["y"] == 5.0


def test_pdf_observer_writes_report_with_test_content(tmp_path: Path):
    settings = ReportSettings(path=tmp_path, name="results")
    observer = PdfObserver(settings, "Device acceptance")
    observer.on_tests_collected(
        [
            TestRecord(
                name="Voltage check",
                description="Measure the supply rail",
                requirements=["REQ-5V"],
                steps=["Connect meter", "Read voltage"],
                outcome="passed",
                duration=0.25,
                logs=[CapturedLog("now", "INFO", "instrument", "Measured 5V")],
                measurements=[
                    MeasurementSeries(
                        name="Voltage over time",
                        x_axis="time",
                        points=[
                            MeasurementPoint("2026-08-29T12:00:00Z", 4.9),
                            MeasurementPoint("2026-08-29T12:00:01Z", 5.0),
                            MeasurementPoint("2026-08-29T12:00:02Z", 5.1),
                        ],
                    ),
                    MeasurementSeries(
                        name="Calibration",
                        x_axis="linear",
                        points=[
                            MeasurementPoint(0.0, 0.01),
                            MeasurementPoint(128.0, 2.5),
                            MeasurementPoint(255.0, 5.0),
                        ],
                    ),
                ],
            )
        ]
    )

    observer.finalize()

    report = tmp_path / "results.pdf"
    assert report.read_bytes().startswith(b"%PDF-")
    assert report.stat().st_size > 1_000
