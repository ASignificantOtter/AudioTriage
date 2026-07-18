from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class SystemEvent:
    timestamp: datetime
    source: str
    message: str


@dataclass(slots=True)
class CorrelationResult:
    likely_cause: str
    evidence: list[str]
    no_correlated_event: bool = False
