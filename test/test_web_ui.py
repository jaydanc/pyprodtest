import threading
from unittest.mock import patch

import pytest

from _pyprodtest.test_record import CapturedLog, TestRecord
from _pyprodtest.web_ui.app import create_app
from _pyprodtest.web_ui.input_acceptor import WebInputAcceptor
from _pyprodtest.web_ui.observer import WebObserver
from _pyprodtest.web_ui.state import LiveState


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


def test_web_observer_promotes_each_running_test_to_the_top():
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
        "Second",
        "First",
        "Third",
    ]

    second.outcome = "passed"
    observer.on_test_end(second)
    third.outcome = "running"
    observer.on_test_run(third)

    assert [test["name"] for test in state.snapshot()["tests"]] == [
        "Third",
        "Second",
        "First",
    ]


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


def test_interrupted_web_input_clears_the_active_prompt():
    state = LiveState()

    with patch.object(state._input_ready, "wait", side_effect=KeyboardInterrupt):
        with pytest.raises(KeyboardInterrupt):
            WebInputAcceptor(state).accept("Continue?", bool)

    assert state.snapshot()["input_request"] is None


def test_web_page_serves_packaged_ui_and_pico_css():
    client = create_app(LiveState()).test_client()

    assert b"PyProdTest" in client.get("/").data
    assert b"--pico-font-family" in client.get("/assets/pico.min.css").data
    script = client.get("/static/app.js").data
    assert b"No logs captured for this test." in script
    assert b'class="chevron"' in script


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
