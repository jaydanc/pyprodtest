"""Jinja-based HTML report observer."""

from collections import Counter
from collections.abc import Sequence
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from _pyprodtest.observers.html_report.report_settings import ReportSettings
from _pyprodtest.observers.test_observer import TestObserver
from _pyprodtest.test_record import TestRecord

TEMPLATE_DIRECTORY = Path(__file__).parent / "templates"
PICO_CSS = Path(__file__).parents[2] / "web_assets" / "pico.min.css"
THEME_CSS = Path(__file__).parents[2] / "web_assets" / "theme.css"


class HtmlObserver(TestObserver):
    """Write a styled, standalone HTML report after the test session."""

    def __init__(self, settings: ReportSettings | str | Path) -> None:
        self.settings = (
            settings
            if isinstance(settings, ReportSettings)
            else ReportSettings.from_output_path(settings)
        )
        self._test_records: list[TestRecord] = []
        environment = Environment(
            loader=FileSystemLoader(TEMPLATE_DIRECTORY),
            autoescape=select_autoescape(("html", "xml")),
        )
        self._template = environment.get_template("report.html")
        self._pico_css = PICO_CSS.read_text(encoding="utf-8")
        self._theme_css = THEME_CSS.read_text(encoding="utf-8")

    def on_tests_collected(self, test_records: Sequence[TestRecord]) -> None:
        self._test_records = list(test_records)

    def on_test_run(self, test_record: TestRecord) -> None:
        pass

    def on_test_end(self, test_record: TestRecord) -> None:
        pass

    def finalize(self) -> None:
        """Write the final report using the latest fixture settings."""
        if not self.settings.enabled:
            return
        output_path = self.settings.output_path
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
            test_records=self._test_records,
            total=total,
            outcomes=outcomes,
            completed=completed,
            progress=(completed / total * 100) if total else 0,
        )
