"""Thread-safe state shared by pytest and the live web application."""

from dataclasses import asdict, dataclass
from threading import Condition, Event, Lock
from uuid import uuid4

from _pyprodtest.test_record import TestRecord


@dataclass(frozen=True)
class InputRequest:
    """An operator prompt currently awaiting a response."""

    id: str
    prompt: str
    input_type: str


class LiveState:
    """Own live records and coordinate blocking operator input."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._input_ready = Condition(self._lock)
        self._records: list[TestRecord] = []
        self._input_request: InputRequest | None = None
        self._input_response: str | bool | None = None
        self._run_complete = False
        self._client_seen = Event()
        self._completion_seen = Event()

    def set_records(self, records: list[TestRecord]) -> None:
        with self._lock:
            self._records = records

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            snapshot = {
                "tests": [asdict(record) for record in self._records],
                "input_request": (
                    asdict(self._input_request) if self._input_request else None
                ),
                "run_complete": self._run_complete,
            }
            self._client_seen.set()
            if self._run_complete:
                self._completion_seen.set()
            return snapshot

    def mark_complete(self) -> None:
        """Publish that no more test updates will be made."""
        with self._lock:
            self._run_complete = True

    def wait_until_complete_is_seen(self, timeout: float) -> None:
        """Give an attached browser a bounded chance to fetch the final state."""
        self._completion_seen.wait(timeout)

    def request_input(
        self, prompt: str, input_type: type[str] | type[bool]
    ) -> str | bool:
        if input_type not in {str, bool}:
            raise TypeError("input_type must be bool or str")

        with self._input_ready:
            self._input_request = InputRequest(
                id=uuid4().hex,
                prompt=prompt,
                input_type="bool" if input_type is bool else "str",
            )
            self._input_response = None
            while self._input_response is None:
                self._input_ready.wait()
            response = self._input_response
            self._input_request = None
            self._input_response = None
            return response

    def respond(self, request_id: str, value: object) -> bool:
        with self._input_ready:
            request = self._input_request
            if request is None or request.id != request_id:
                return False
            if request.input_type == "bool":
                if not isinstance(value, bool):
                    return False
            elif not isinstance(value, str):
                return False
            self._input_response = value
            self._input_ready.notify()
            return True
