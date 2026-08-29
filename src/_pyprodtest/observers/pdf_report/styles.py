"""Shared styles and summary components for PDF reports."""

from collections import Counter

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Table, TableStyle

OUTCOME_COLORS = {
    "passed": colors.HexColor("#15803d"),
    "failed": colors.HexColor("#b91c1c"),
    "skipped": colors.HexColor("#a16207"),
    "running": colors.HexColor("#0369a1"),
    "pending": colors.HexColor("#64748b"),
}


def report_styles() -> dict[str, ParagraphStyle]:
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


def summary_table(
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
