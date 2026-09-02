# Configuration

PyProdTest reads `pyprodtest.yaml` from the pytest project root. Every setting
is optional.

```yaml
name: Device acceptance
loop: false

ui:
  enabled: true
  host: 127.0.0.1
  port: 8765

reports:
  output: reports/device-acceptance
  html: true
  json: true
  csv: true
  pdf: true

test_order:
  - identify_test.py
  - status_test.py::test_status_light
```

## Top-level settings

| Setting | Default | Purpose |
| --- | --- | --- |
| `name` | `Production test execution` | Live UI heading and browser title |
| `loop` | `false` | Repeat the collected test sequence until pytest is stopped |
| `test_order` | all collected tests | Ordered list of filenames or filename node IDs |

## Looped Mode

Set `loop: true` to repeat the collected, ordered test plan until pytest is
stopped:

```yaml
name: Device acceptance
loop: true

test_order:
  - identify_test.py
  - status_test.py
```

The UI keeps completed passes in its History sidebar. Test state and the DUT
identifier reset for each pass, and session-scoped fixtures are finalized
between passes. See [Looped runs](reports.md#looped-runs) for report naming and
overwrite behavior.

## Test Order

The `test_order` list is an ordering hint. PyProdTest matches entries against the
collected test filename, not the full path. Entries that do not match any
collected test are ignored, and collected tests that are not listed still run
after the listed tests in their normal pytest order.

## Live UI

| Setting | Default | Purpose |
| --- | --- | --- |
| `ui.enabled` | `true` | Start the browser UI and use web input |
| `ui.host` | `127.0.0.1` | Interface on which the server listens |
| `ui.port` | `8765` | Server port; use `0` for a free port |

The default host exposes the UI only on the local machine. Port `0` is useful
when a fixed port is unavailable, but prevents browser-tab reuse between runs.

## Reports

| Setting | Default | Purpose |
| --- | --- | --- |
| `reports.output` | `pyprodtest-report` | Extensionless output path and base name |
| `reports.html` | `true` | Generate an HTML report |
| `reports.json` | `true` | Generate a JSON report |
| `reports.csv` | `true` | Generate a CSV report |
| `reports.pdf` | `true` | Generate a PDF report |

For output naming, per-DUT folders, timestamps, and loop behavior, see
[Reports](reports.md).

!!! warning "Binding beyond localhost"
    Changing `ui.host` to a network-visible interface exposes the operator page
    to that network. Use an appropriate trusted environment; the early-stage UI
    is not an authenticated public service.
