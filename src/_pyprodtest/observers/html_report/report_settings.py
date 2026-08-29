"""Mutable configuration exposed by the report fixture."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ReportSettings:
    """Control whether and where the final HTML report is written."""

    path: str | Path = Path(".")
    name: str = "pyprodtest-report.html"
    enabled: bool = True

    @property
    def output_path(self) -> Path:
        """Return the configured report directory and name as one path."""
        return Path(self.path) / self.name

    @classmethod
    def from_output_path(cls, output_path: str | Path) -> "ReportSettings":
        output_path = Path(output_path)
        return cls(path=output_path.parent, name=output_path.name)
