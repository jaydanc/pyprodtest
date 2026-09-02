"""Paginated PDF report observer."""

from collections import Counter
from collections.abc import Sequence
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

from _pyprodtest.config import ReportsConfig
from _pyprodtest.observers.pdf_report.sections import test_section
from _pyprodtest.observers.pdf_report.styles import report_styles, summary_table
from _pyprodtest.observers.test_observer import TestObserver
from _pyprodtest.test_record import TestRecord


class PdfObserver(TestObserver):
    """Write a polished PDF report after the test session."""

    def __init__(
        self,
        settings: ReportsConfig,
    ) -> None:
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
        """Write one PDF report for a completed loop run."""
        self._wrote_loop_report = True
        self._write(self.settings.output_path)

    def on_tests_finished(self) -> None:
        """Write the final PDF using the latest fixture settings."""
        if self._wrote_loop_report:
            return
        self._write(self.settings.output_path)

    def _write(self, output_path: Path) -> None:
        """Write the final PDF using the latest fixture settings."""
        if not self.settings.enabled:
            return
        if output_path.suffix.casefold() != ".pdf":
            output_path = output_path.parent / f"{output_path.name}.pdf"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self._build(output_path)

    def _build(self, output_path: Path) -> None:
        document = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=22 * mm,
            bottomMargin=18 * mm,
            title=self.settings.dut_id or "Unknown DUT",
            author="PyProdTest",
        )
        document.build(
            self._story(report_styles()),
            onFirstPage=self._draw_page,
            onLaterPages=self._draw_page,
        )

    def _story(self, styles: dict[str, ParagraphStyle]) -> list[object]:
        outcomes = Counter(record.outcome for record in self._test_records)
        story: list[object] = [
            Paragraph(escape(self.settings.dut_id or "Unknown DUT"), styles["title"]),
            Paragraph("Production test report", styles["subtitle"]),
            Spacer(1, 7 * mm),
            summary_table(outcomes, len(self._test_records), styles),
            Spacer(1, 8 * mm),
            HRFlowable(color=colors.HexColor("#cbd5e1"), thickness=0.6),
            Spacer(1, 4 * mm),
        ]
        if not self._test_records:
            story.append(Paragraph("No tests were collected.", styles["muted"]))
            return story

        for index, record in enumerate(self._test_records):
            if index:
                story.extend([Spacer(1, 5 * mm), HRFlowable(), Spacer(1, 5 * mm)])
            story.extend(test_section(record, index + 1, styles))
        return story

    def _draw_page(self, canvas, document) -> None:
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#e2e8f0"))
        canvas.line(18 * mm, 15 * mm, A4[0] - 18 * mm, 15 * mm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(18 * mm, 10 * mm, "PyProdTest")
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {document.page}")
        canvas.restoreState()
