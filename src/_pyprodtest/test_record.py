"""
Data structure to hold test metadata.
"""

from dataclasses import dataclass, field


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
