import pytest
from .decorators import *
from . import web_ui
from .measurement import Measurement

_config = None  # global pytest config reference


@pytest.fixture
def input(request):
    if request.config.getoption("--ui"):
        return web_ui.get_input
    return lambda question: True  # headless fallback


@pytest.fixture(scope="function")
def measure(request):
    records = []

    # Reset measurements for this test
    try:
        web_ui.reset_measurements(request.node.name)
    except Exception:
        pass

    def _measure(value, unit, validator=None, name=""):
        m = Measurement(name, value, unit, validator)
        records.append(m)
        # broadcast live update
        try:
            web_ui.update_measurement(
                test_name=request.node.name,
                name=name or "unnamed",
                value=value,
                unit=str(unit),
            )
        except Exception:
            pass
        return m

    yield _measure

    # validate and assert after test finishes
    failed = []
    for m in records:
        m.validate()
        if not m.valid:
            failed.append(f"{m.name}: {m.reason or 'invalid value'} ({m.value}{m.unit})")

    if failed:
        raise AssertionError("Measurements failed validation:\n" + "\n".join(failed))


def pytest_addoption(parser):
    parser.addoption("--ui", action="store_true", help="Run with web UI")


def pytest_configure(config):
    global _config
    _config = config
    if config.getoption("--ui"):
        web_ui.start_ui()
    config._test_metadata = []


def pytest_runtest_call(item):
    meta = {
        "nodeid": item.nodeid,
        "name": getattr(item.function, "_test_meta", {}).get("name"),
        "desc": getattr(item.function, "_test_meta", {}).get("desc"),
        "requirements": getattr(item.function, "_requirements", []),
        "steps": getattr(item.function, "_steps", []),
        "result": None,
    }
    item.config._test_metadata.append(meta)


def pytest_runtest_logreport(report):
    from .reporting import generate_report

    if report.when in ("call", "teardown") and _config is not None:
        nodeid = getattr(report, "nodeid", None)
        for meta in _config._test_metadata:
            if meta.get("nodeid") == nodeid or meta.get("name") in nodeid:
                meta["result"] = "passed" if report.passed else "failed"
                if not report.passed:
                    meta["failure_reason"] = str(getattr(report, "longreprtext", ""))
                generate_report(meta)
                try:
                    web_ui.update_report(meta)
                except Exception:
                    pass
                break


def pytest_terminal_summary(terminalreporter, config):
    import time

    terminalreporter.write_line("PyProdTest report written to pyprodtest_report.json")
    terminalreporter.write_line("Web UI running at http://localhost:5000 — press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
