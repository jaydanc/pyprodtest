"""Tabular CSV report observer."""

import csv
import json
from collections.abc import Sequence
from dataclasses import asdict

from _pyprodtest.observers.test_observer import TestObserver
from _pyprodtest.report_settings import ReportSettings
from _pyprodtest.test_record import TestRecord

FIELDNAMES = (
    "name",
    "description",
    "nodeid",
    "outcome",
    "duration",
    "requirements",
    "steps",
    "failure_reason",
    "logs",
    "measurements",
)


class CsvObserver(TestObserver):
    """Write one lossless, spreadsheet-friendly row per test."""

    def __init__(self, settings: ReportSettings) -> None:
        self.settings = settings
        self._test_records: list[TestRecord] = []

    def on_tests_collected(self, test_records: Sequence[TestRecord]) -> None:
        self._test_records = list(test_records)

    def on_test_run(self, test_record: TestRecord) -> None:
        pass

    def on_test_end(self, test_record: TestRecord) -> None:
        pass

    def finalize(self) -> None:
        """Write the CSV report when reporting is enabled."""
        if not self.settings.enabled:
            return
        output_path = self.settings.output_path.parent / (
            f"{self.settings.output_path.name}.csv"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8", newline="") as report_file:
            writer = csv.DictWriter(report_file, fieldnames=FIELDNAMES)
            writer.writeheader()
            for record in self._test_records:
                writer.writerow(
                    {
                        "name": record.name,
                        "description": record.description,
                        "nodeid": record.nodeid,
                        "outcome": record.outcome,
                        "duration": record.duration,
                        "requirements": json.dumps(record.requirements),
                        "steps": json.dumps(record.steps),
                        "failure_reason": record.failure_reason,
                        "logs": json.dumps(
                            [asdict(log) for log in record.logs], ensure_ascii=False
                        ),
                        "measurements": json.dumps(
                            [asdict(series) for series in record.measurements],
                            ensure_ascii=False,
                        ),
                    }
                )
