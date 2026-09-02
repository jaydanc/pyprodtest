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

The session-scoped `report` fixture changes the destination for all enabled
formats:

```python
def test_identify_device(input, report) -> None:
    serial = input("Device serial number")
    report.path = f"reports/{serial}"
    report.name = "acceptance"
    report.enabled = True
```

The observers use the latest values when they write. Set
`report.enabled = False` to suppress the current run; format selection remains
in `pyprodtest.yaml`.

## Put each DUT report in its own folder

The `dut` fixture gives the device under test (DUT) a human-readable identifier
in the live UI and generated reports. Combine it with the `report` fixture when
the identifier should also determine the output path:

```python
from datetime import datetime
from pathlib import Path


def test_identify_device(input, dut, report) -> None:
    dut_id = input("DUT serial number")
    dut(dut_id)

    timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    report.path = Path("reports") / dut_id
    report.name = f"{dut_id}_{timestamp}"
```

For a DUT identified as `SN-1234`, this produces a PDF such as:

```text
reports/SN-1234/SN-1234_20260902-142305.pdf
```

The same base path is used for every enabled format. To generate only PDF,
disable the other formats:

```yaml
reports:
  html: false
  json: false
  csv: false
  pdf: true
```

Only use trusted or validated text in a path. If an operator enters the DUT ID,
reject path separators and other characters that are not valid for your naming
scheme.

## Output path behavior

`report.path` is the directory and `report.name` is the base filename.
`reports.output` combines both into one extensionless path. Observers add their
own extensions, and PyProdTest creates missing parent directories.

PyProdTest does not add a timestamp automatically. Add one to `report.name`, as
shown above, when files must be unique. Keep generated reports out of
source-controlled test fixtures and ignore them in version control.

## Looped runs

When `loop: true` is configured, reports are written after every full pass
through the collected tests using the `report.path` and `report.name` values
set during that pass. PyProdTest does not add a pass number or timestamp. If the
same path is reused, the next pass overwrites the previous report.

Set a unique name while identifying each DUT to keep every pass, for example:

```text
reports/SN-1234/SN-1234_20260902-142305.pdf
reports/SN-1235/SN-1235_20260902-142419.pdf
```

At the start of every pass, test outcomes, logs, measurements, and the DUT
identifier are cleared. Identify the DUT and set any dynamic report path during
every pass. Session-scoped fixtures are finalized between passes.

Stop the loop with the usual pytest interruption (for example, Ctrl+C). Only a
completed pass produces a report.
