# Reports

PyProdTest writes enabled report formats at pytest session shutdown. Every
format is derived from the same collected `TestRecord` state, including test
metadata, lifecycle outcome, failure information, captured logs, and measured
data.

HTML reports display each named measurement series as a chart. JSON reports
preserve measurements as nested series and points. CSV reports store the same
structure as JSON in the `measurements` column so no points are lost.

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

The latest fixture values at session shutdown are used by all report observers.
Set `report.enabled = False` to suppress every report for that run. Individual
format selection remains controlled by `pyprodtest.yaml`.

## Output path behavior

`report.path` is the directory and `report.name` is the extensionless base
name. PyProdTest appends the session timestamp and the observer's extension.
Create report directories outside source-controlled test fixtures when
possible, and ignore them in version control.
