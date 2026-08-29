"""Test-level flowables for PDF reports."""

from html import escape

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    CondPageBreak,
    LongTable,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from _pyprodtest.observers.pdf_report.charts import measurement_chart
from _pyprodtest.observers.pdf_report.styles import OUTCOME_COLORS
from _pyprodtest.test_record import TestRecord


def test_section(
    record: TestRecord, number: int, styles: dict[str, ParagraphStyle]
) -> list[object]:
    flowables = _test_heading(record, number, styles)
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
                    escape(record.failure_reason).replace("\n", "<br/>"), styles["body"]
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
    if record.measurements:
        flowables.append(
            Paragraph(f"MEASUREMENTS ({len(record.measurements)})", styles["label"])
        )
        for series in record.measurements:
            flowables.extend(
                [
                    CondPageBreak(78 * mm),
                    Spacer(1, 12 * mm),
                    Paragraph(escape(series.name), styles["body"]),
                    Spacer(1, 1.5 * mm),
                    measurement_chart(series),
                    Spacer(1, 2 * mm),
                ]
            )
    return flowables


def _test_heading(
    record: TestRecord, number: int, styles: dict[str, ParagraphStyle]
) -> list[object]:
    status_color = OUTCOME_COLORS.get(
        record.outcome.casefold(), colors.HexColor("#64748b")
    )
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
    return [heading]


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
        rows, colWidths=[42 * mm, 18 * mm, 38 * mm, 59 * mm], repeatRows=1
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
    if "T" not in timestamp:
        return escape(timestamp)
    date, time = timestamp.split("T", 1)
    return f"{escape(date)}<br/>{escape(time)}"
