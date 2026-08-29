"""Measurement recording API used by the pytest fixture."""

from collections.abc import Callable
from datetime import datetime
from numbers import Real

from _pyprodtest.test_record import MeasurementPoint, MeasurementSeries, TestRecord


class Plot:
    """Record explicit X/Y points in one named series."""

    def __init__(self, record: TestRecord, name: str) -> None:
        self._series = _series(record, name, "linear")

    def add(self, x: Real, y: Real) -> None:
        """Add one numeric X/Y point to the plot."""
        self._series.points.append(
            MeasurementPoint(x=_number(x, "x"), y=_number(y, "y"))
        )


class Measure:
    """Record values against time or create explicit X/Y plots."""

    def __init__(self, get_record: Callable[[], TestRecord]) -> None:
        self._get_record = get_record

    def __call__(self, value: Real, name: str) -> None:
        """Record a numeric value against the current timestamp."""
        series = _series(self._get_record(), name, "time")
        series.points.append(
            MeasurementPoint(
                x=datetime.now().astimezone().isoformat(timespec="milliseconds"),
                y=_number(value, "value"),
            )
        )

    def plot(self, name: str) -> Plot:
        """Return a plot that accepts explicit numeric X/Y points."""
        return Plot(self._get_record(), name)


def _series(record: TestRecord, name: str, x_axis: str) -> MeasurementSeries:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("measurement name must be a non-empty string")
    for series in record.measurements:
        if series.name == name:
            if series.x_axis != x_axis:
                raise ValueError(
                    f"measurement {name!r} already uses a different X axis"
                )
            return series
    series = MeasurementSeries(name=name, x_axis=x_axis)
    record.measurements.append(series)
    return series


def _number(value: Real, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{field_name} must be a real number")
    return float(value)
