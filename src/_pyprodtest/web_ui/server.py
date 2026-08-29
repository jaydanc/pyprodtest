"""Lifecycle wrapper for the live web server."""

import logging
import threading
import webbrowser

from werkzeug.serving import BaseWSGIServer, make_server

from _pyprodtest.web_ui.app import create_app
from _pyprodtest.web_ui.input_acceptor import WebInputAcceptor
from _pyprodtest.web_ui.observer import WebObserver
from _pyprodtest.web_ui.state import LiveState

EXISTING_BROWSER_WAIT_SECONDS = 0.75


class WebUi:
    """Compose the observer, input provider, and background HTTP server."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8765) -> None:
        self.host = host
        self.state = LiveState()
        self.observer = WebObserver(self.state)
        self.input_acceptor = WebInputAcceptor(self.state)
        self._server: BaseWSGIServer = make_server(
            host, port, create_app(self.state), threaded=True
        )
        self.port = self._server.server_port
        self._thread: threading.Thread | None = None
        self._werkzeug_logger = logging.getLogger("werkzeug")
        self._werkzeug_log_level = self._werkzeug_logger.level

    @property
    def url(self) -> str:
        display_host = "127.0.0.1" if self.host in {"0.0.0.0", "::"} else self.host
        return f"http://{display_host}:{self.port}/"

    def start(self, *, open_browser: bool = False) -> None:
        if self._werkzeug_log_level < logging.WARNING:
            self._werkzeug_logger.setLevel(logging.WARNING)
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="pyprodtest-web-ui",
            daemon=True,
        )
        self._thread.start()
        if open_browser and not self.state.wait_for_client(
            EXISTING_BROWSER_WAIT_SECONDS
        ):
            webbrowser.open(self.url)

    def finish_and_stop(self) -> None:
        """Publish the final state before stopping the background server."""
        self.state.mark_complete()
        self.state.wait_until_complete_is_seen(timeout=1)
        self.stop()

    def stop(self) -> None:
        """Stop the background server immediately."""
        try:
            self._server.shutdown()
            if self._thread is not None:
                self._thread.join(timeout=5)
            self._server.server_close()
        finally:
            self._werkzeug_logger.setLevel(self._werkzeug_log_level)
