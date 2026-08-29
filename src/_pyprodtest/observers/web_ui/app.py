"""Flask routes for the live operator UI."""

from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request

from _pyprodtest.observers.web_ui.state import LiveState

PICO_CSS = Path(__file__).parents[2] / "web_assets" / "pico.min.css"
THEME_CSS = Path(__file__).parents[2] / "web_assets" / "theme.css"


def create_app(state: LiveState) -> Flask:
    """Create an HTTP application around an injected live state."""
    app = Flask(__name__)

    @app.get("/")
    def index() -> str:
        state.note_client()
        return render_template("index.html")

    @app.get("/assets/pico.min.css")
    def pico_css() -> Response:
        return Response(PICO_CSS.read_bytes(), mimetype="text/css")

    @app.get("/assets/theme.css")
    def theme_css() -> Response:
        return Response(THEME_CSS.read_bytes(), mimetype="text/css")

    @app.get("/api/state")
    def get_state() -> Response:
        return jsonify(state.snapshot())

    @app.post("/api/input/<request_id>")
    def submit_input(request_id: str) -> tuple[Response, int] | Response:
        body = request.get_json(silent=True) or {}
        if not state.respond(request_id, body.get("value")):
            return jsonify(error="Input request is stale or the value is invalid."), 409
        return jsonify(accepted=True)

    return app
