import pytest

from _pyprodtest import hooks
from _pyprodtest.measure import Measure
from _pyprodtest.test_record import TestRecord


def test_measure_records_timestamped_values_in_one_named_series():
    record = TestRecord(name="Voltage test")
    measure = Measure(lambda: record)

    measure(4.98, "Voltage", "V")
    measure(5.01, "Voltage", "V")

    assert len(record.measurements) == 1
    series = record.measurements[0]
    assert series.name == "Voltage"
    assert series.x_axis == "time"
    assert series.unit == "V"
    assert [point.y for point in series.points] == [4.98, 5.01]
    assert all(isinstance(point.x, str) for point in series.points)


def test_measure_plot_records_explicit_xy_values():
    record = TestRecord(name="Calibration test")
    plot = Measure(lambda: record).plot("Calibration", y_unit="V", x_unit="DAC")

    plot.add(0, 0.02)
    plot.add(128, 2.51)

    series = record.measurements[0]
    assert series.x_axis == "linear"
    assert series.unit == "V"
    assert series.x_unit == "DAC"
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

    with pytest.raises(ValueError, match="already uses unit"):
        measure(5.1, "Voltage", "V")
    with pytest.raises(TypeError, match="unit must be a string"):
        measure(5.1, "Current", 1)

    plot = measure.plot("Sweep", y_unit="V", x_unit="DAC")
    plot.add(1, 2)
    with pytest.raises(ValueError, match="already uses X unit"):
        measure.plot("Sweep", y_unit="V", x_unit="step")
    with pytest.raises(TypeError, match="X unit must be a string"):
        measure.plot("Other sweep", x_unit=1)


def test_measure_fixture_attaches_data_to_the_current_test(measure, request):
    measure(3.3, "Supply", "V")

    record = hooks._state.records[request.node.nodeid]
    assert record.measurements[0].points[0].y == 3.3
    assert record.measurements[0].unit == "V"


def test_dut_fixture_sets_report_dut_identifier(dut):
    try:
        assert dut("SN-1234") == "SN-1234"
        assert hooks._state.config.reports.dut_id == "SN-1234"
    finally:
        hooks._state.config.reports.dut_id = None


def test_dut_fixture_rejects_non_string(dut):
    with pytest.raises(TypeError, match="dut_id must be a string"):
        dut(1234)
