"""Pytest fixtures provided by the PyProdTest plugin."""

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

import pytest

from _pyprodtest.config import ReportsConfig
from _pyprodtest.input_acceptors import TestInput
from _pyprodtest.measure import Measure
from _pyprodtest.test_record import TestRecord

LOGGING = logging.getLogger(__name__)

if TYPE_CHECKING:
    from _pyprodtest.hooks import PluginState


def _plugin_state() -> "PluginState":
    from _pyprodtest import hooks

    return hooks.get_plugin_state()


@pytest.fixture(scope="session")
def report() -> ReportsConfig:
    """Return mutable settings for the final standalone HTML report."""
    return _plugin_state().config.reports


@pytest.fixture(scope="session")
def dut() -> Callable[[str], str]:
    """Set the device under test identifier for reports and the live UI."""

    def set_dut_id(dut_id: str) -> str:
        if not isinstance(dut_id, str):
            raise TypeError("dut_id must be a string")
        _plugin_state().config.reports.dut_id = dut_id
        return dut_id

    return set_dut_id


@pytest.fixture(scope="session")
def input(request: pytest.FixtureRequest) -> TestInput:
    """Return input from the acceptor selected by the plugin's run mode."""
    state = _plugin_state()

    def accept(prompt: str, input_type: type[str] | type[bool] = str) -> str | bool:
        capture_manager = request.config.pluginmanager.get_plugin("capturemanager")
        if capture_manager is None:
            return state.input_acceptor.accept(prompt, input_type)

        # pytest's standard disabled-capture context leaves stdin blocked.
        # Explicitly include stdin while suspending capture for the prompt.
        capture_manager.suspend(in_=True)
        try:
            response = state.input_acceptor.accept(prompt, input_type)
            LOGGING.info("Received input for prompt '%s': %s", prompt, response)
            return response
        finally:
            capture_manager.resume()

    return accept


@pytest.fixture
def measure(request: pytest.FixtureRequest) -> Measure:
    """Record numeric data for the current test and live operator UI."""

    def get_record() -> TestRecord:
        state = _plugin_state()
        record = state.records.get(request.node.nodeid)
        if record is None:
            raise RuntimeError("The current test has no PyProdTest record")
        return record

    return Measure(get_record)
