# Configuration

PyProdTest reads `pyprodtest.yaml` from the pytest project root. Every setting
is optional.

```yaml
name: Device acceptance

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

tests:
  - test/identify_test.py
  - test/status_test.py::test_status_light
```

## Top-level settings

| Setting | Default | Purpose |
| --- | --- | --- |
| `name` | `Production test execution` | Live UI heading and browser title |
| `tests` | all collected tests | Ordered list of test paths or node IDs |

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
