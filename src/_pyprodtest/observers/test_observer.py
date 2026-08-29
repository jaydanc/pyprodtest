"""Observer interface for receiving test lifecycle events."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from _pyprodtest.test_record import TestRecord


class TestObserver(ABC):
    """Receives test records from the pytest integration layer."""

    __test__ = False

    @abstractmethod
    def on_tests_collected(self, test_records: Sequence[TestRecord]) -> None:
        """Handle the complete set of collected tests."""

    @abstractmethod
    def on_test_run(self, test_record: TestRecord) -> None:
        """Handle a test immediately before its call phase."""

    @abstractmethod
    def on_test_end(self, test_record: TestRecord) -> None:
        """Handle a test after all of its pytest phases have ended."""
