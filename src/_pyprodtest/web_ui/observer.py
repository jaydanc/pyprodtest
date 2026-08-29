"""Test observer that publishes domain records to the live state."""

from collections.abc import Sequence

from _pyprodtest.observers.test_observer import TestObserver
from _pyprodtest.test_record import TestRecord
from _pyprodtest.web_ui.state import LiveState


class WebObserver(TestObserver):
    """Expose test records without depending on pytest or HTTP details."""

    def __init__(self, state: LiveState) -> None:
        self._state = state

    def on_tests_collected(self, test_records: Sequence[TestRecord]) -> None:
        self._state.set_records(list(test_records))

    def on_test_run(self, test_record: TestRecord) -> None:
        pass

    def on_test_end(self, test_record: TestRecord) -> None:
        pass
