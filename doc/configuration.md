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

Set `loop: true` when the same production-test plan should run continuously:

```yaml
name: Device acceptance
loop: true

test_order:
  - identify_test.py
  - status_test.py
```

PyProdTest collects the tests once, applies `test_order`, then repeats that
ordered list until pytest is stopped. The live web UI shows the current pass as
active and keeps previous passes in its History sidebar for the lifetime of the
browser session.

At the end of every pass, PyProdTest asks pytest to tear down any remaining
setup state before the next pass starts. That means session-scoped fixture
finalizers run between loop passes, and the next pass reinitializes those
fixtures when tests request them again.

Enabled reports are written after every completed pass. The normal timestamped
base name is kept, and each pass adds a run suffix before the extension, for
example `reports/device-acceptance-20260829-140507-run-0001.html`.

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

A session timestamp is appended to the base name before each observer adds its
extension. For example, `reports/device-acceptance` becomes
`reports/device-acceptance-20260829-140507.html` and matching JSON, CSV, and PDF
files.

!!! warning "Binding beyond localhost"
    Changing `ui.host` to a network-visible interface exposes the operator page
    to that network. Use an appropriate trusted environment; the early-stage UI
    is not an authenticated public service.
