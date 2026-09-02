# Reports

PyProdTest writes enabled report formats at pytest session shutdown, or after
each completed pass when `loop: true` is configured. Every format is derived
from the same collected `TestRecord` state, including test metadata, lifecycle
outcome, failure information, captured logs, and measured data.

HTML reports display each named measurement series as a chart. JSON reports
preserve measurements as nested series and points. CSV reports store the same
structure as JSON in the `measurements` column so no points are lost. PDF
reports include compact vector charts for each measurement series.

## Choose formats and destination

Use project-level YAML for the normal report policy:

```yaml
reports:
  output: reports/acceptance
  html: true
  json: true
  csv: false
  pdf: true
```

## Adjust the output during a run

The session-scoped `report` fixture changes the final destination:

```python
def test_identify_device(input, report) -> None:
    serial = input("Device serial number")
    report.path = f"reports/{serial}"
    report.name = "acceptance"
    report.enabled = True
```

The latest fixture values at the time reports are written are used by all report
observers. Set `report.enabled = False` to suppress reports for that run.
Individual format selection remains controlled by `pyprodtest.yaml`.

## Output path behavior

`report.path` is the directory and `report.name` is the extensionless base
name. PyProdTest appends the session timestamp and the observer's extension.
Create report directories outside source-controlled test fixtures when
possible, and ignore them in version control.

## Looped runs

When `loop: true` is configured, reports are written after every full pass
through the collected tests. PyProdTest keeps the session timestamped base name
and inserts a zero-padded run suffix before the extension:

```text
reports/acceptance-20260829-140507-run-0001.html
reports/acceptance-20260829-140507-run-0001.json
reports/acceptance-20260829-140507-run-0002.html
reports/acceptance-20260829-140507-run-0002.json
```

Session-scoped fixture finalizers run before these per-run reports are announced
to observers and before the next pass starts. The next pass reinitializes
session fixtures when tests request them again.
