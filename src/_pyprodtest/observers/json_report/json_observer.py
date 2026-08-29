"""Structured JSON report observer."""

import json
from collections import Counter
from collections.abc import Sequence
from dataclasses import asdict

from _pyprodtest.observers.test_observer import TestObserver
from _pyprodtest.report_settings import ReportSettings
from _pyprodtest.test_record import TestRecord


class JsonObserver(TestObserver):
    """Write complete test records to a final JSON report."""

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
        """Write the JSON report when reporting is enabled."""
        if not self.settings.enabled:
            return
        output_path = self.settings.output_path.parent / (
            f"{self.settings.output_path.name}.json"
        )
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
