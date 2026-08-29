"""Input acceptors used to obtain operator decisions during tests."""

from abc import ABC, abstractmethod
from typing import Protocol, overload


class TestInput(Protocol):
    """Callable interface exposed to tests by the ``input`` fixture."""

    @overload
    def __call__(self, prompt: str, input_type: type[str] = str) -> str: ...

    @overload
    def __call__(self, prompt: str, input_type: type[bool]) -> bool: ...

    def __call__(
        self, prompt: str, input_type: type[str] | type[bool] = str
    ) -> bool | str: ...


class InputAcceptor(ABC):
    """Interface for an operator-facing source of test input."""

    @overload
    def accept(self, prompt: str, input_type: type[str] = str) -> str: ...

    @overload
    def accept(self, prompt: str, input_type: type[bool]) -> bool: ...

    @abstractmethod
    def accept(
        self, prompt: str, input_type: type[str] | type[bool] = str
    ) -> bool | str:
        """Ask an operator for a value of ``input_type``."""


class ConsoleInputAcceptor(InputAcceptor):
    """Obtain operator decisions from the process console."""

    @overload
    def accept(self, prompt: str, input_type: type[str] = str) -> str: ...

    @overload
    def accept(self, prompt: str, input_type: type[bool]) -> bool: ...

    def accept(
        self, prompt: str, input_type: type[str] | type[bool] = str
    ) -> bool | str:
        """Read text once, or prompt until receiving an unambiguous yes/no."""
        print("\n")

        if input_type is str:
            return input(f"{prompt}: ")
        if input_type is not bool:
            raise TypeError("input_type must be bool or str")

        while True:
            response = input(f"{prompt} [y/n]: ").strip().casefold()
            if response in {"y", "yes"}:
                return True
            if response in {"n", "no"}:
                return False
            print("Please answer 'yes' or 'no'.")
