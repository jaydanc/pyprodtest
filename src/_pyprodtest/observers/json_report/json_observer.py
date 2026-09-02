"""Structured JSON report observer."""

import json
from collections import Counter
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

from _pyprodtest.config import ReportsConfig
from _pyprodtest.observers.test_observer import TestObserver
from _pyprodtest.test_record import TestRecord


class JsonObserver(TestObserver):
    """Write complete test records to a final JSON report."""

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
        """Write one JSON report for a completed loop run."""
        self._wrote_loop_report = True
        self._write(self.settings.output_path)

    def on_tests_finished(self) -> None:
        """Write the JSON report when reporting is enabled."""
        if self._wrote_loop_report:
            return
        self._write(self.settings.output_path)

    def _write(self, output_path: Path) -> None:
        """Write the JSON report when reporting is enabled."""
        if not self.settings.enabled:
            return
        output_path = output_path.parent / f"{output_path.name}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        outcomes = Counter(record.outcome for record in self._test_records)
        document = {
            "summary": {
                "total": len(self._test_records),
                "outcomes": dict(outcomes),
            },
            "tests": [asdict(record) for record in self._test_records],
        }
        output_path.write_text(
            json.dumps(document, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
