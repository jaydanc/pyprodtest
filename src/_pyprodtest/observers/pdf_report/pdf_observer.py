"""Paginated PDF report observer."""

from collections import Counter
from collections.abc import Sequence
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    LongTable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from _pyprodtest.observers.test_observer import TestObserver
from _pyprodtest.report_settings import ReportSettings
from _pyprodtest.test_record import TestRecord

OUTCOME_COLORS = {
    "passed": colors.HexColor("#15803d"),
    "failed": colors.HexColor("#b91c1c"),
    "skipped": colors.HexColor("#a16207"),
    "running": colors.HexColor("#0369a1"),
    "pending": colors.HexColor("#64748b"),
}


class PdfObserver(TestObserver):
    """Write a polished PDF report after the test session."""

    def __init__(
        self,
        settings: ReportSettings | str | Path,
        title: str = "Production test report",
    ) -> None:
        self.settings = (
            settings
            if isinstance(settings, ReportSettings)
            else ReportSettings.from_output_path(settings)
        )
        self.title = title
        self._test_records: list[TestRecord] = []

    def on_tests_collected(self, test_records: Sequence[TestRecord]) -> None:
        self._test_records = list(test_records)

    def on_test_run(self, test_record: TestRecord) -> None:
        pass

    def on_test_end(self, test_record: TestRecord) -> None:
        pass

    def finalize(self) -> None:
        """Write the final PDF using the latest fixture settings."""
        if not self.settings.enabled:
            return
        output_path = self.settings.output_path
        if output_path.suffix.casefold() != ".pdf":
            output_path = output_path.parent / f"{output_path.name}.pdf"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self._build(output_path)

    def _build(self, output_path: Path) -> None:
        styles = _styles()
        document = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=22 * mm,
            bottomMargin=18 * mm,
            title=self.title,
            author="PyProdTest",
        )
        story = self._story(styles)
        document.build(
            story,
            onFirstPage=self._draw_page,
            onLaterPages=self._draw_page,
        )

    def _story(self, styles: dict[str, ParagraphStyle]) -> list[object]:
        outcomes = Counter(record.outcome for record in self._test_records)
        story: list[object] = [
            Paragraph(escape(self.title), styles["title"]),
            Paragraph("Production test report", styles["subtitle"]),
            Spacer(1, 7 * mm),
            _summary_table(outcomes, len(self._test_records), styles),
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
            story.extend(_test_section(record, index + 1, styles))
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


def _styles() -> dict[str, ParagraphStyle]:
    sample = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=sample["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=29,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=2 * mm,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=sample["Normal"],
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#64748b"),
        ),
        "heading": ParagraphStyle(
            "TestHeading",
            parent=sample["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=2 * mm,
        ),
        "label": ParagraphStyle(
            "Label",
            parent=sample["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#475569"),
            spaceBefore=3 * mm,
            spaceAfter=1 * mm,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=sample["BodyText"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#1e293b"),
        ),
        "small": ParagraphStyle(
            "Small",
            parent=sample["BodyText"],
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#334155"),
        ),
        "muted": ParagraphStyle(
            "Muted",
            parent=sample["BodyText"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#64748b"),
        ),
        "summary": ParagraphStyle(
            "Summary",
            parent=sample["Normal"],
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.white,
        ),
        "status": ParagraphStyle(
            "Status",
            parent=sample["Normal"],
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=colors.white,
        ),
    }


def _summary_table(
    outcomes: Counter[str], total: int, styles: dict[str, ParagraphStyle]
) -> Table:
    values = [("Total", total, colors.HexColor("#334155"))]
    values.extend(
        (label.title(), outcomes[label], OUTCOME_COLORS[label])
        for label in ("passed", "failed", "skipped")
    )
    cells = [
        Paragraph(f"{value}<br/><font size='7'>{label}</font>", styles["summary"])
        for label, value, _ in values
    ]
    table = Table([cells], colWidths=[39 * mm] * 4, rowHeights=[18 * mm])
    commands = [("VALIGN", (0, 0), (-1, -1), "MIDDLE")]
    commands.extend(
        ("BACKGROUND", (index, 0), (index, 0), color)
        for index, (_, _, color) in enumerate(values)
    )
    table.setStyle(TableStyle(commands))
    return table


def _test_section(
    record: TestRecord, number: int, styles: dict[str, ParagraphStyle]
) -> list[object]:
    outcome = record.outcome.casefold()
    status_color = OUTCOME_COLORS.get(outcome, colors.HexColor("#64748b"))
    heading = Table(
        [
            [
                Paragraph(f"{number}. {escape(record.name)}", styles["heading"]),
                Paragraph(escape(record.outcome.upper()), styles["status"]),
            ]
        ],
        colWidths=[129 * mm, 28 * mm],
    )
    heading.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (1, 0), (1, 0), status_color),
                ("BOX", (1, 0), (1, 0), 0, status_color),
                ("LEFTPADDING", (0, 0), (0, 0), 0),
                ("RIGHTPADDING", (0, 0), (0, 0), 4 * mm),
            ]
        )
    )
    flowables: list[object] = [heading]
    if record.description:
        flowables.append(Paragraph(escape(record.description), styles["body"]))
    if record.nodeid:
        flowables.append(Paragraph(escape(record.nodeid), styles["muted"]))
    flowables.append(Paragraph(f"Duration: {record.duration:.3f}s", styles["small"]))
    if record.requirements:
        flowables.extend(
            [
                Paragraph("REQUIREMENTS", styles["label"]),
                Paragraph(", ".join(map(escape, record.requirements)), styles["body"]),
            ]
        )
    if record.steps:
        flowables.append(Paragraph("STEPS", styles["label"]))
        flowables.extend(
            Paragraph(f"{index}. {escape(step)}", styles["body"])
            for index, step in enumerate(record.steps, 1)
        )
    if record.failure_reason:
        flowables.extend(
            [
                Paragraph("FAILURE DETAILS", styles["label"]),
                Paragraph(
                    escape(record.failure_reason).replace("\n", "<br/>"),
                    styles["body"],
                ),
            ]
        )
    if record.logs:
        flowables.extend(
            [
                Paragraph(f"LOGS ({len(record.logs)})", styles["label"]),
                _logs_table(record, styles),
            ]
        )
    return flowables


def _logs_table(record: TestRecord, styles: dict[str, ParagraphStyle]) -> LongTable:
    rows = [["Time", "Level", "Logger", "Message"]]
    rows.extend(
        [
            Paragraph(_display_timestamp(log.timestamp), styles["small"]),
            Paragraph(escape(log.level), styles["small"]),
            Paragraph(escape(log.logger), styles["small"]),
            Paragraph(escape(log.message), styles["small"]),
        ]
        for log in record.logs
    )
    table = LongTable(
        rows,
        colWidths=[42 * mm, 18 * mm, 38 * mm, 59 * mm],
        repeatRows=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#334155")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 7.5),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f8fafc")],
                ),
                ("LEFTPADDING", (0, 0), (-1, -1), 2 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 1.5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5 * mm),
            ]
        )
    )
    return table


def _display_timestamp(timestamp: str) -> str:
    """Split ISO timestamps at the date boundary for predictable table wrapping."""
    if "T" not in timestamp:
        return escape(timestamp)
    date, time = timestamp.split("T", 1)
    return f"{escape(date)}<br/>{escape(time)}"
