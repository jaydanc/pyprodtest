"""Tabular CSV report observer."""

import csv
import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

from _pyprodtest.config import ReportsConfig
from _pyprodtest.observers.test_observer import TestObserver
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

    def __init__(self, settings: ReportsConfig) -> None:
        self.settings = settings
        self._test_records: list[TestRecord] = []
        self._wrote_loop_report = False

    def on_tests_start(self) -> None:
        pass

    def on_tests_collected(self, test_records: Sequence[TestRecord]) -> None:
        self._test_records = list(test_records)

    def on_test_run(self, test_record: TestRecord) -> None:
        pass

    def on_test_end(self, test_record: TestRecord) -> None:
        pass

    def on_loop_tests_start(self, run_index):
        pass

    def on_loop_tests_finished(self, run_index: int) -> None:
        """Write one CSV report for a completed loop run."""
        self._wrote_loop_report = True
        self._write(self.settings.output_path)

    def on_tests_finished(self) -> None:
        """Write the CSV report when reporting is enabled."""
        if self._wrote_loop_report:
            return
        self._write(self.settings.output_path)

    def _write(self, output_path: Path) -> None:
        """Write the CSV report when reporting is enabled."""
        if not self.settings.enabled:
            return
        output_path = output_path.parent / f"{output_path.name}.csv"
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
