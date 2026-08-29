"""Operator input implementation backed by the live web state."""

from typing import overload

from _pyprodtest.input_acceptors import InputAcceptor
from _pyprodtest.web_ui.state import LiveState


class WebInputAcceptor(InputAcceptor):
    """Wait for an operator response submitted through the web UI."""

    def __init__(self, state: LiveState) -> None:
        self._state = state

    @overload
    def accept(self, prompt: str, input_type: type[str] = str) -> str: ...

    @overload
    def accept(self, prompt: str, input_type: type[bool]) -> bool: ...

    def accept(
        self, prompt: str, input_type: type[str] | type[bool] = str
    ) -> str | bool:
        return self._state.request_input(prompt, input_type)
