"""Thread-safe state shared by pytest and the live web application."""

from collections import Counter
from dataclasses import asdict, dataclass
from threading import Condition, Event, Lock
from uuid import uuid4

from _pyprodtest.config import ReportsConfig
from _pyprodtest.test_record import TestRecord

INPUT_WAIT_INTERVAL_SECONDS = 0.1


@dataclass(frozen=True)
class InputRequest:
    """An operator prompt currently awaiting a response."""

    id: str
    prompt: str
    input_type: str


class LiveState:
    """Own live records and coordinate blocking operator input."""

    def __init__(self, reports: ReportsConfig | None = None) -> None:
        self._lock = Lock()
        self._input_ready = Condition(self._lock)
        self._reports = reports or ReportsConfig()
        self._records: list[TestRecord] = []
        self._input_request: InputRequest | None = None
        self._input_response: str | bool | None = None
        self._run_index = 1
        self._history: list[dict[str, object]] = []
        self._run_complete = False
        self._client_seen = Event()
        self._completion_seen = Event()

    def set_records(self, records: list[TestRecord]) -> None:
        with self._lock:
            self._records = records

    def start_run(self, run_index: int) -> None:
        """Publish the active run number for looped sessions."""
        with self._lock:
            self._run_index = run_index

    def archive_current_run(self, run_index: int) -> None:
        """Keep a final snapshot for one completed run in the live UI."""
        with self._lock:
            dut_id = self._reports.dut_id
            tests = [asdict(record) for record in self._records]
            self._history.insert(
                0,
                {
                    "id": f"run-{run_index}",
                    "label": dut_id or "Unknown DUT",
                    "run_index": run_index,
                    "dut_id": dut_id,
                    "summary": _summarize(tests),
                    "tests": tests,
                },
            )

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            dut_id = self._reports.dut_id
            tests = [asdict(record) for record in self._records]
            snapshot = {
                "run_index": self._run_index,
                "dut_id": dut_id,
                "current_run": {
                    "id": f"run-{self._run_index}",
                    "label": dut_id or "Unknown DUT",
                    "run_index": self._run_index,
                    "dut_id": dut_id,
                    "summary": _summarize(tests),
                },
                "history": list(self._history),
                "tests": tests,
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

    def note_client(self) -> None:
        """Record that an operator page has connected to this run."""
        self._client_seen.set()

    def wait_for_client(self, timeout: float) -> bool:
        """Wait briefly for an existing operator page to reconnect."""
        return self._client_seen.wait(timeout)

    def wait_until_complete_is_seen(self, timeout: float) -> None:
        """Give an attached browser a bounded chance to fetch the final state."""
        if self._client_seen.is_set():
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
            try:
                while self._input_response is None:
                    # A bounded wait lets the main pytest thread process Ctrl+C,
                    # including on platforms where an indefinite lock wait is not
                    # signal-interruptible.
                    self._input_ready.wait(INPUT_WAIT_INTERVAL_SECONDS)
                return self._input_response
            finally:
                self._input_request = None
                self._input_response = None

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


def _summarize(tests: list[dict[str, object]]) -> dict[str, int]:
    outcomes = Counter(str(test.get("outcome", "pending")) for test in tests)
    completed = sum(outcomes[outcome] for outcome in ("passed", "failed", "skipped"))
    return {
        "total": len(tests),
        "complete": completed,
        "passed": outcomes["passed"],
        "failed": outcomes["failed"],
        "skipped": outcomes["skipped"],
        "pending": outcomes["pending"],
        "running": outcomes["running"],
    }
