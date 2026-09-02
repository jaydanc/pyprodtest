import threading
from unittest.mock import patch

import pytest

from _pyprodtest.config import ReportsConfig
from _pyprodtest.observers.web_ui.app import create_app
from _pyprodtest.observers.web_ui.input_acceptor import WebInputAcceptor
from _pyprodtest.observers.web_ui.observer import WebObserver
from _pyprodtest.observers.web_ui.state import LiveState
from _pyprodtest.test_record import (
    CapturedLog,
    MeasurementPoint,
    MeasurementSeries,
    TestRecord,
)


def test_web_observer_exposes_live_record_updates():
    state = LiveState()
    observer = WebObserver(state)
    record = TestRecord(name="Live test", nodeid="test_live")

    observer.on_tests_collected([record])
    record.outcome = "running"
    record.logs.append(CapturedLog("now", "INFO", "instrument", "Ready"))

    test = state.snapshot()["tests"][0]
    assert test["outcome"] == "running"
    assert test["logs"][0]["message"] == "Ready"


def test_web_observer_keeps_plan_order_while_tests_run():
    state = LiveState()
    observer = WebObserver(state)
    first = TestRecord(name="First")
    second = TestRecord(name="Second")
    third = TestRecord(name="Third")
    observer.on_tests_collected([first, second, third])

    first.outcome = "passed"
    observer.on_test_end(first)
    second.outcome = "running"
    observer.on_test_run(second)

    assert [test["name"] for test in state.snapshot()["tests"]] == [
        "First",
        "Second",
        "Third",
    ]

    second.outcome = "passed"
    observer.on_test_end(second)
    third.outcome = "running"
    observer.on_test_run(third)

    assert [test["name"] for test in state.snapshot()["tests"]] == [
        "First",
        "Second",
        "Third",
    ]


def test_web_observer_owns_server_state_and_input_acceptor():
    state = LiveState()
    observer = WebObserver(state, port=0)

    with patch("webbrowser.open") as open_browser:
        observer.on_tests_start()

    assert observer.input_acceptor._state is state
    assert observer.url.startswith("http://127.0.0.1:")
    assert open_browser.call_count == 0

    observer.on_tests_finished()

    assert state.snapshot()["run_complete"] is True
    assert observer._server is None


def test_web_observer_keeps_completed_run_history_for_looped_runs():
    state = LiveState()
    observer = WebObserver(state)
    record = TestRecord(name="Voltage", nodeid="test_voltage")
    observer.on_tests_collected([record])

    observer.on_loop_tests_start(1)
    record.outcome = "passed"
    record.duration = 0.2
    observer.on_loop_tests_finished(1)
    record.outcome = "pending"
    record.duration = 0.0
    observer.on_loop_tests_start(2)

    snapshot = state.snapshot()

    assert snapshot["current_run"]["label"] == "Run 2"
    assert snapshot["current_run"]["summary"]["pending"] == 1
    assert snapshot["history"][0]["label"] == "Run 1"
    assert snapshot["history"][0]["summary"]["passed"] == 1
    assert snapshot["history"][0]["tests"][0]["outcome"] == "passed"


def test_live_state_uses_report_dut_id_for_active_and_history_runs():
    reports = ReportsConfig()
    state = LiveState(reports)
    record = TestRecord(name="Voltage", nodeid="test_voltage")
    state.set_records([record])
    state.start_run(1)

    reports.dut_id = "SN-1234"
    active = state.snapshot()
    state.archive_current_run(1)
    history = state.snapshot()["history"][0]

    assert active["dut_id"] == "SN-1234"
    assert active["current_run"]["dut_id"] == "SN-1234"
    assert active["current_run"]["label"] == "SN-1234"
    assert history["dut_id"] == "SN-1234"
    assert history["label"] == "SN-1234"


def test_web_observer_shares_report_dut_id_with_live_state():
    reports = ReportsConfig()
    observer = WebObserver(reports=reports)

    reports.dut_id = "SN-5678"

    assert observer.state.snapshot()["dut_id"] == "SN-5678"


def test_web_input_acceptor_blocks_until_valid_http_response():
    state = LiveState()
    app = create_app(state)
    result: list[str | bool] = []
    worker = threading.Thread(
        target=lambda: result.append(WebInputAcceptor(state).accept("Continue?", bool))
    )
    worker.start()

    client = app.test_client()
    request_id = _wait_for_input(client)["id"]
    assert (
        client.post(f"/api/input/{request_id}", json={"value": "yes"}).status_code
        == 409
    )
    assert (
        client.post(f"/api/input/{request_id}", json={"value": True}).status_code == 200
    )
    worker.join(timeout=1)

    assert result == [True]


def test_web_input_acceptor_preserves_multiline_prompts_in_state():
    state = LiveState()
    app = create_app(state)
    result: list[str | bool] = []
    worker = threading.Thread(
        target=lambda: result.append(
            WebInputAcceptor(state).accept("Is this \n on a different \n line?", bool)
        )
    )
    worker.start()

    client = app.test_client()
    prompt = _wait_for_input(client)

    assert prompt["prompt"] == "Is this \n on a different \n line?"
    assert (
        client.post(f"/api/input/{prompt['id']}", json={"value": True}).status_code
        == 200
    )
    worker.join(timeout=1)

    assert result == [True]


def test_interrupted_web_input_clears_the_active_prompt():
    state = LiveState()

    with patch.object(state._input_ready, "wait", side_effect=KeyboardInterrupt):
        with pytest.raises(KeyboardInterrupt):
            WebInputAcceptor(state).accept("Continue?", bool)

    assert state.snapshot()["input_request"] is None


def test_web_page_serves_packaged_ui_and_pico_css():
    client = create_app(LiveState()).test_client()

    page = client.get("/").data
    assert b"PyProdTest" in page
    assert b'<script type="module" src="/static/app.js"></script>' in page
    assert b'<script defer src="/assets/alpine.min.js"></script>' in page
    assert b'x-data="pyprodtestDashboard()"' in page
    assert b"x-for=" in page
    assert b"x-text=" in page
    assert b"history-sidebar" in page
    assert b"history.length" in page
    assert b"operator-prompt" in page
    assert b"promptLines(inputRequest?.prompt)" in page
    assert b"dutId || 'Operator console'" in page
    assert b'x-text="runTitle"' in page
    assert b'<br x-show="index > 0">' in page
    assert b"--pico-font-family" in client.get("/assets/pico.min.css").data
    assert b"--app-bg" in client.get("/assets/theme.css").data
    charts_js = client.get("/static/charts.js")
    assert charts_js.status_code == 200
    assert charts_js.mimetype == "text/javascript"
    assert b"export function chartsRenderVisible" in charts_js.data
    assert b"new Chart(canvas" in charts_js.data
    assert b"series.points.map((point) => point.y)" in charts_js.data
    assert b"Boolean(series.unit)" in charts_js.data
    assert b"Boolean(series.x_unit)" in charts_js.data
    app_js = client.get("/static/app.js")
    assert app_js.status_code == 200
    assert app_js.mimetype == "text/javascript"
    assert app_js.headers["Cache-Control"] == "no-cache, max-age=0"
    assert b"import {" in app_js.data
    assert b'from "./charts.js"' in app_js.data
    assert b"window.pyprodtestDashboard" in app_js.data
    assert b"defaultRunTitle" in app_js.data
    assert b"dutId = state.dut_id || null" in app_js.data
    assert b"document.title = `${this.runTitle}" in app_js.data
    assert b"promptLines" in app_js.data
    assert b"runSummaryText" in app_js.data
    assert b"data-chart-key" in page
    assert b"chartsRenderVisible(this.tests)" in app_js.data
    assert b"chartsRefresh($el)" in page
    assert b"liveDuration(activeTest)" in page
    assert b"activeTimer" in app_js.data
    assert b"/assets/chart.umd.min.js" in page
    chart_js = client.get("/assets/chart.umd.min.js")
    assert chart_js.mimetype == "application/javascript"
    assert b"Chart.js v4.4.7" in chart_js.data
    alpine_js = client.get("/assets/alpine.min.js")
    assert alpine_js.mimetype == "application/javascript"
    assert b"Alpine" in alpine_js.data


def test_live_state_serializes_measurement_series_for_the_chart():
    state = LiveState()
    state.set_records(
        [
            TestRecord(
                name="Voltage",
                measurements=[
                    MeasurementSeries(
                        name="Output voltage",
                        x_axis="time",
                        unit="V",
                        x_unit="",
                        points=[MeasurementPoint(x="2026-08-29T12:00:00Z", y=5.02)],
                    )
                ],
            )
        ]
    )

    measurement = (
        create_app(state)
        .test_client()
        .get("/api/state")
        .get_json()["tests"][0]["measurements"][0]
    )

    assert measurement == {
        "name": "Output voltage",
        "x_axis": "time",
        "unit": "V",
        "x_unit": "",
        "points": [{"x": "2026-08-29T12:00:00Z", "y": 5.02}],
    }


def test_web_page_uses_configured_name_in_heading_and_browser_title():
    response = create_app(LiveState(), "Device <Acceptance>").test_client().get("/")

    assert (
        b"<title>Device &lt;Acceptance&gt; \xc2\xb7 PyProdTest</title>" in response.data
    )
    assert b'<h1 id="run-title" x-text="runTitle">Unknown DUT</h1>' in response.data


def test_final_state_is_available_before_server_shutdown():
    state = LiveState()
    client = create_app(state).test_client()
    record = TestRecord(name="Failed test", outcome="failed")
    state.set_records([record])

    assert client.get("/api/state").get_json()["run_complete"] is False
    state.mark_complete()
    final_state = client.get("/api/state").get_json()

    assert final_state["run_complete"] is True
    assert final_state["tests"][0]["outcome"] == "failed"


def test_shutdown_waits_for_attached_page_to_fetch_final_state():
    state = LiveState()
    client = create_app(state).test_client()
    client.get("/")
    state.mark_complete()
    finished = threading.Event()
    waiter = threading.Thread(
        target=lambda: (state.wait_until_complete_is_seen(1), finished.set())
    )

    waiter.start()
    assert not finished.wait(0.01)
    assert client.get("/api/state").get_json()["run_complete"] is True

    waiter.join(timeout=1)
    assert finished.is_set()


def test_existing_page_can_reconnect_to_a_new_run():
    state = LiveState()
    connected = threading.Event()

    def wait_for_page() -> None:
        if state.wait_for_client(1):
            connected.set()

    waiter = threading.Thread(target=wait_for_page)
    waiter.start()
    state.note_client()
    waiter.join(timeout=1)

    assert connected.is_set()


def _wait_for_input(client):
    for _ in range(100):
        prompt = client.get("/api/state").get_json()["input_request"]
        if prompt is not None:
            return prompt
    raise AssertionError("input request was not published")
