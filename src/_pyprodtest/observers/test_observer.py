"""Observer interface for receiving test lifecycle events."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from _pyprodtest.test_record import TestRecord


class TestObserver(ABC):
    """Receives test records from the pytest integration layer."""

    __test__ = False

    @abstractmethod
    def on_tests_start(self) -> None:
        """Handle the event when the test session starts."""

    @abstractmethod
    def on_tests_collected(self, test_records: Sequence[TestRecord]) -> None:
        """Handle the complete set of collected tests."""

    @abstractmethod
    def on_loop_tests_start(self, run_index: int) -> None:
        """Handle the start of one loop pass through all collected tests.

        Called only for configured loop runs, before any test item is executed.
        Observers can use this to publish the active run number or prepare
        per-run state without changing normal one-shot pytest sessions.

        WARNING: on_tests_start will also be called
        """

    @abstractmethod
    def on_loop_tests_finished(self, run_index: int) -> None:
        """Handle the end of one completed loop pass through all collected tests.

        Called only after a full loop pass finishes and pytest's setup state has
        been torn down, so session-scoped fixture finalizers have run before
        observers snapshot history or write per-run reports.

        WARNING: on_tests_finished will also be called
        """

    @abstractmethod
    def on_test_run(self, test_record: TestRecord) -> None:
        """Handle a test immediately before its call phase."""

    @abstractmethod
    def on_test_end(self, test_record: TestRecord) -> None:
        """Handle a test after all of its pytest phases have ended."""

    @abstractmethod
    def on_tests_finished(self) -> None:
        """Handle the event when all tests have finished."""
