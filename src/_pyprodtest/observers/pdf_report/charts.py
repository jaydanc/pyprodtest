"""Vector measurement charts for PDF reports."""

from reportlab.graphics.shapes import Circle, Drawing, Line, PolyLine, Rect, String
from reportlab.lib import colors
from reportlab.lib.units import mm

from _pyprodtest.test_record import MeasurementSeries


def measurement_chart(series: MeasurementSeries) -> Drawing:
    """Build a dependency-free vector line chart for one measurement series."""
    width = 157 * mm
    height = 58 * mm
    drawing = Drawing(width, height)
    drawing.add(
        Rect(
            0,
            0,
            width,
            height,
            rx=2 * mm,
            ry=2 * mm,
            fillColor=colors.HexColor("#f8fafc"),
            strokeColor=colors.HexColor("#cbd5e1"),
            strokeWidth=0.6,
        )
    )
    if not series.points:
        drawing.add(
            String(
                width / 2,
                height / 2,
                "No measured points",
                textAnchor="middle",
                fontName="Helvetica",
                fontSize=8,
                fillColor=colors.HexColor("#64748b"),
            )
        )
        return drawing

    left, bottom, plot_width, plot_height = 14 * mm, 10 * mm, 137 * mm, 36 * mm
    x_values = _x_values(series)
    y_values = [point.y for point in series.points]
    x_bounds = _axis_bounds(x_values)
    y_bounds = _axis_bounds(y_values)
    _add_grid(drawing, left, bottom, plot_width, plot_height, y_bounds)
    _add_series(
        drawing,
        series,
        x_values,
        y_values,
        x_bounds,
        y_bounds,
        left,
        bottom,
        plot_width,
        plot_height,
    )
    _add_x_labels(drawing, series, x_values, left, plot_width)
    drawing.add(
        String(
            left + plot_width,
            height - 5 * mm,
            f"Latest: {_axis_label(y_values[-1])}",
            textAnchor="end",
            fontName="Helvetica-Bold",
            fontSize=7.5,
            fillColor=colors.HexColor("#0369a1"),
        )
    )
    return drawing


def _x_values(series: MeasurementSeries) -> list[float]:
    if series.x_axis == "time":
        return [float(index) for index, _ in enumerate(series.points)]
    return [float(point.x) for point in series.points]


def _add_grid(
    drawing: Drawing,
    left: float,
    bottom: float,
    width: float,
    height: float,
    y_bounds: tuple[float, float],
) -> None:
    y_min, y_max = y_bounds
    for tick in range(5):
        fraction = tick / 4
        y = bottom + fraction * height
        value = y_min + fraction * (y_max - y_min)
        drawing.add(
            Line(
                left,
                y,
                left + width,
                y,
                strokeColor=colors.HexColor("#e2e8f0"),
                strokeWidth=0.5,
            )
        )
        drawing.add(
            String(
                left - 2 * mm,
                y - 2,
                _axis_label(value),
                textAnchor="end",
                fontName="Helvetica",
                fontSize=6.5,
                fillColor=colors.HexColor("#64748b"),
            )
        )
    drawing.add(
        Line(
            left,
            bottom,
            left,
            bottom + height,
            strokeColor=colors.HexColor("#94a3b8"),
            strokeWidth=0.7,
        )
    )
    drawing.add(
        Line(
            left,
            bottom,
            left + width,
            bottom,
            strokeColor=colors.HexColor("#94a3b8"),
            strokeWidth=0.7,
        )
    )


def _add_series(
    drawing: Drawing,
    series: MeasurementSeries,
    x_values: list[float],
    y_values: list[float],
    x_bounds: tuple[float, float],
    y_bounds: tuple[float, float],
    left: float,
    bottom: float,
    width: float,
    height: float,
) -> None:
    x_min, x_max = x_bounds
    y_min, y_max = y_bounds
    coordinates: list[float] = []
    for x_value, y_value in zip(x_values, y_values, strict=True):
        x = left + (x_value - x_min) / (x_max - x_min) * width
        y = bottom + (y_value - y_min) / (y_max - y_min) * height
        coordinates.extend((x, y))
        if len(series.points) <= 40:
            drawing.add(
                Circle(
                    x, y, 1.1, fillColor=colors.HexColor("#0284c7"), strokeColor=None
                )
            )
    if len(series.points) > 1:
        drawing.add(
            PolyLine(
                coordinates, strokeColor=colors.HexColor("#0284c7"), strokeWidth=1.4
            )
        )


def _add_x_labels(
    drawing: Drawing,
    series: MeasurementSeries,
    x_values: list[float],
    left: float,
    width: float,
) -> None:
    first, last = _x_labels(series, x_values)
    for x, label, anchor in ((left, first, "start"), (left + width, last, "end")):
        drawing.add(
            String(
                x,
                3.5 * mm,
                label,
                textAnchor=anchor,
                fontName="Helvetica",
                fontSize=6.5,
                fillColor=colors.HexColor("#64748b"),
            )
        )


def _axis_bounds(values: list[float]) -> tuple[float, float]:
    minimum, maximum = min(values), max(values)
    if minimum == maximum:
        padding = max(abs(minimum) * 0.05, 0.5)
        return minimum - padding, maximum + padding
    padding = (maximum - minimum) * 0.05
    return minimum - padding, maximum + padding


def _axis_label(value: float) -> str:
    return f"{value:.4g}"


def _x_labels(series: MeasurementSeries, x_values: list[float]) -> tuple[str, str]:
    if series.x_axis != "time":
        return _axis_label(x_values[0]), _axis_label(x_values[-1])
    return _short_time(str(series.points[0].x)), _short_time(str(series.points[-1].x))


def _short_time(timestamp: str) -> str:
    if "T" not in timestamp:
        return timestamp
    return timestamp.split("T", 1)[1][:8]
