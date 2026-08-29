"""Jinja-based HTML report observer."""

from collections import Counter
from collections.abc import Sequence
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from _pyprodtest.observers.test_observer import TestObserver
from _pyprodtest.test_record import TestRecord

TEMPLATE_DIRECTORY = Path(__file__).parent / "templates"
PICO_CSS = Path(__file__).parents[2] / "web_assets" / "pico.min.css"


class HtmlObserver(TestObserver):
    """Write a styled, standalone HTML report as test state changes."""

    def __init__(self, output_path: str | Path) -> None:
        self.output_path = Path(output_path)
        self._test_records: list[TestRecord] = []
        environment = Environment(
            loader=FileSystemLoader(TEMPLATE_DIRECTORY),
            autoescape=select_autoescape(("html", "xml")),
        )
        self._template = environment.get_template("report.html")
        self._pico_css = PICO_CSS.read_text(encoding="utf-8")

    def on_tests_collected(self, test_records: Sequence[TestRecord]) -> None:
        self._test_records = list(test_records)
        self._write_report()

    def on_test_run(self, test_record: TestRecord) -> None:
        self._write_report()

    def on_test_end(self, test_record: TestRecord) -> None:
        self._write_report()

    def _write_report(self) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(self._render(), encoding="utf-8")

    def _render(self) -> str:
        outcomes = Counter(record.outcome for record in self._test_records)
        return self._template.render(
            pico_css=self._pico_css,
            test_records=self._test_records,
            total=len(self._test_records),
            outcomes=outcomes,
        )
