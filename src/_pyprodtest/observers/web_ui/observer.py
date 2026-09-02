"""Test observer that publishes domain records to the live state."""

import logging
import threading
import webbrowser
from collections.abc import Sequence

from werkzeug.serving import BaseWSGIServer, make_server

from _pyprodtest.config import ReportsConfig
from _pyprodtest.observers.test_observer import TestObserver
from _pyprodtest.observers.web_ui.app import create_app
from _pyprodtest.observers.web_ui.input_acceptor import WebInputAcceptor
from _pyprodtest.observers.web_ui.state import LiveState
from _pyprodtest.test_record import TestRecord

EXISTING_BROWSER_WAIT_SECONDS = 0.75
LOGGER = logging.getLogger(__name__)


class WebObserver(TestObserver):
    """Publish records and operator input through a live web server."""

    def __init__(
        self,
        state: LiveState | None = None,
        *,
        host: str = "127.0.0.1",
        port: int = 8765,
        name: str = "Unknown Project",
        open_browser: bool = False,
        reports: ReportsConfig | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.name = name
        self.open_browser = open_browser
        self.state = state or LiveState(reports)
        self.input_acceptor = WebInputAcceptor(self.state)
        self._server: BaseWSGIServer | None = None
        self._thread: threading.Thread | None = None
        self._werkzeug_logger = logging.getLogger("werkzeug")
        self._werkzeug_log_level = self._werkzeug_logger.level

    @property
    def url(self) -> str:
        display_host = "127.0.0.1" if self.host in {"0.0.0.0", "::"} else self.host
        return f"http://{display_host}:{self.port}/"

    def on_tests_start(self) -> None:
        if self._server is not None:
            return
        if self._werkzeug_log_level < logging.WARNING:
            self._werkzeug_logger.setLevel(logging.WARNING)
        self._server = make_server(
            self.host, self.port, create_app(self.state, self.name), threaded=True
        )
        self.port = self._server.server_port
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="pyprodtest-web-ui",
            daemon=True,
        )
        self._thread.start()
        LOGGER.info("PyProdTest web UI: %s", self.url)
        if self.open_browser and not self.state.wait_for_client(
            EXISTING_BROWSER_WAIT_SECONDS
        ):
            webbrowser.open(self.url)

    def on_tests_collected(self, test_records: Sequence[TestRecord]) -> None:
        self.state.set_records(list(test_records))

    def on_loop_tests_start(self, run_index: int) -> None:
        self.state.start_run(run_index)

    def on_loop_tests_finished(self, run_index: int) -> None:
        self.state.archive_current_run(run_index)

    def on_test_run(self, test_record: TestRecord) -> None:
        pass

    def on_test_end(self, test_record: TestRecord) -> None:
        pass

    def on_tests_finished(self) -> None:
        """Publish the final state before stopping the background server."""
        self.state.mark_complete()
        self.state.wait_until_complete_is_seen(timeout=1)
        self.stop()

    def stop(self) -> None:
        """Stop the background server immediately."""
        try:
            if self._server is not None:
                self._server.shutdown()
                if self._thread is not None:
                    self._thread.join(timeout=5)
                self._server.server_close()
        finally:
            self._server = None
            self._thread = None
            self._werkzeug_logger.setLevel(self._werkzeug_log_level)
