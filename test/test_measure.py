import pytest

from _pyprodtest import hooks
from _pyprodtest.measure import Measure
from _pyprodtest.test_record import TestRecord


def test_measure_records_timestamped_values_in_one_named_series():
    record = TestRecord(name="Voltage test")
    measure = Measure(lambda: record)

    measure(4.98, "Voltage")
    measure(5.01, "Voltage")

    assert len(record.measurements) == 1
    series = record.measurements[0]
    assert series.name == "Voltage"
    assert series.x_axis == "time"
    assert [point.y for point in series.points] == [4.98, 5.01]
    assert all(isinstance(point.x, str) for point in series.points)


def test_measure_plot_records_explicit_xy_values():
    record = TestRecord(name="Calibration test")
    plot = Measure(lambda: record).plot("Calibration")

    plot.add(0, 0.02)
    plot.add(128, 2.51)

    series = record.measurements[0]
    assert series.x_axis == "linear"
    assert [(point.x, point.y) for point in series.points] == [
        (0.0, 0.02),
        (128.0, 2.51),
    ]


def test_measure_rejects_non_numeric_values_and_axis_name_collisions():
    record = TestRecord(name="Invalid measurement")
    measure = Measure(lambda: record)

    with pytest.raises(TypeError, match="value must be a real number"):
        measure("5.0", "Voltage")

    measure(5.0, "Voltage")
    with pytest.raises(ValueError, match="different X axis"):
        measure.plot("Voltage")


def test_measure_fixture_attaches_data_to_the_current_test(measure):
    measure(3.3, "Supply")

    record = hooks._state.records[
        "test_measure.py::test_measure_fixture_attaches_data_to_the_current_test"
    ]
    assert record.measurements[0].points[0].y == 3.3
