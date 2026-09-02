"""Jinja-based HTML report observer."""

from collections import Counter
from collections.abc import Sequence
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from _pyprodtest.config import ReportsConfig
from _pyprodtest.observers.test_observer import TestObserver
from _pyprodtest.test_record import TestRecord

TEMPLATE_DIRECTORY = Path(__file__).parent / "templates"
PICO_CSS = Path(__file__).parents[2] / "web_assets" / "pico.min.css"
THEME_CSS = Path(__file__).parents[2] / "web_assets" / "theme.css"
CHART_JS = Path(__file__).parents[2] / "web_assets" / "chart.umd.min.js"


class HtmlObserver(TestObserver):
    """Write a styled, standalone HTML report after the test session."""

    def __init__(self, settings: ReportsConfig) -> None:
        self.settings = settings
        self._test_records: list[TestRecord] = []
        self._wrote_run_report = False
        environment = Environment(
            loader=FileSystemLoader(TEMPLATE_DIRECTORY),
            autoescape=select_autoescape(("html", "xml")),
        )
        self._template = environment.get_template("report.html")
        self._pico_css = PICO_CSS.read_text(encoding="utf-8")
        self._theme_css = THEME_CSS.read_text(encoding="utf-8")
        self._chart_js = CHART_JS.read_text(encoding="utf-8")

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
        """Write one HTML report for a completed loop run."""
        self._wrote_run_report = True
        self._write(
            self.settings.output_path.with_name(
                f"{self.settings.output_path.stem}_run_{run_index}"
            )
        )

    def on_tests_finished(self) -> None:
        """Write the final report using the latest fixture settings."""
        if self._wrote_run_report:
            return
        self._write(self.settings.output_path)

    def _write(self, output_path: Path) -> None:
        """Write the final report using the latest fixture settings."""
        if not self.settings.enabled:
            return
        if output_path.suffix.casefold() != ".html":
            output_path = output_path.parent / f"{output_path.name}.html"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self._render(), encoding="utf-8")

    def _render(self) -> str:
        outcomes = Counter(record.outcome for record in self._test_records)
        completed = sum(
            outcomes[outcome] for outcome in ("passed", "failed", "skipped")
        )
        total = len(self._test_records)
        return self._template.render(
            pico_css=self._pico_css,
            theme_css=self._theme_css,
            chart_js=self._chart_js,
            test_records=self._test_records,
            total=total,
            outcomes=outcomes,
            completed=completed,
            progress=(completed / total * 100) if total else 0,
            dutId=self.settings.dut_id,
        )
