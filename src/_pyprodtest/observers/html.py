"""Simple HTML report observer."""

from collections.abc import Sequence
from html import escape
from pathlib import Path

from _pyprodtest.observers.test_observer import TestObserver
from _pyprodtest.test_record import TestRecord


class HtmlObserver(TestObserver):
    """Writes a standalone HTML report as test state changes."""

    def __init__(self, output_path: str | Path) -> None:
        self.output_path = Path(output_path)
        self._test_records: list[TestRecord] = []

    def on_tests_collected(self, test_records: Sequence[TestRecord]) -> None:
        self._test_records = list(test_records)
        self._write_report()

    def on_test_run(self, test_record: TestRecord) -> None:
        self._write_report()

    def on_test_end(self, test_record: TestRecord) -> None:
        self._write_report()

    def _write_report(self) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(self._render(), encoding="utf-8")

    def _render(self) -> str:
        rows = "\n".join(
            self._render_test(test_record) for test_record in self._test_records
        )
        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PyProdTest report</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #202124; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #dadce0; padding: 0.6rem; text-align: left; }}
    th {{ background: #f1f3f4; }}
    .passed {{ color: #137333; }}
    .failed {{ color: #c5221f; }}
    .running {{ color: #b06000; }}
    pre {{ margin: 0; white-space: pre-wrap; overflow-wrap: anywhere; }}
    .logs {{ margin: 0; padding-left: 1.2rem; }}
    .log-time, .log-level, .log-name {{ color: #5f6368; }}
  </style>
</head>
<body>
  <h1>PyProdTest report</h1>
  <table>
    <thead><tr><th>Test</th><th>Description</th><th>Requirements</th><th>Steps</th><th>Outcome</th><th>Logs</th><th>Failure reason</th><th>Duration</th></tr></thead>
    <tbody>
{rows}
    </tbody>
  </table>
</body>
</html>
"""

    @staticmethod
    def _render_test(test_record: TestRecord) -> str:
        requirements = ", ".join(test_record.requirements)
        steps = " → ".join(test_record.steps)
        logs = "".join(
            "<li>"
            f'<span class="log-time">{escape(log.timestamp)}</span> '
            f'<span class="log-level">{escape(log.level)}</span> '
            f'<span class="log-name">{escape(log.logger)}</span>: '
            f"{escape(log.message)}"
            "</li>"
            for log in test_record.logs
        )
        return (
            "      <tr>"
            f"<td>{escape(test_record.name)}</td>"
            f"<td>{escape(test_record.description)}</td>"
            f"<td>{escape(requirements)}</td>"
            f"<td>{escape(steps)}</td>"
            f'<td class="{escape(test_record.outcome)}">'
            f"{escape(test_record.outcome)}</td>"
            f'<td><ul class="logs">{logs}</ul></td>'
            f"<td><pre>{escape(test_record.failure_reason)}</pre></td>"
            f"<td>{test_record.duration:.3f}s</td>"
            "</tr>"
        )
