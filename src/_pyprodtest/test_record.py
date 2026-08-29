"""
Data structure to hold test metadata.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class CapturedLog:
    """One log entry emitted while a test was active."""

    timestamp: str
    level: str
    logger: str
    message: str

    @classmethod
    def from_record(cls, record: logging.LogRecord) -> "CapturedLog":
        return cls(
            timestamp=datetime.fromtimestamp(record.created)
            .astimezone()
            .isoformat(timespec="milliseconds"),
            level=record.levelname,
            logger=record.name,
            message=record.getMessage(),
        )


@dataclass
class TestRecord:
    """Metadata and run state for one collected pytest test."""

    __test__ = False

    name: str
    description: str = ""
    requirements: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    nodeid: str = ""
    outcome: str = "pending"
    duration: float = 0.0
    failure_reason: str = ""
    logs: list[CapturedLog] = field(default_factory=list)
