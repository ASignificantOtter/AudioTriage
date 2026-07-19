from __future__ import annotations

import re
from collections import deque
from collections.abc import Iterable
from datetime import datetime

from .models import IncidentCandidate

_PATTERN_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("buffer_underrun", re.compile(r"underrun|overload", re.IGNORECASE)),
    ("device_disconnect", re.compile(r"device.*(removed|disconnect)", re.IGNORECASE)),
    ("sample_rate_mismatch", re.compile(r"sample.?rate.*mismatch", re.IGNORECASE)),
    ("driver_restart", re.compile(r"coreaudiod.*(restart|relaunch)", re.IGNORECASE)),
    ("cpu_thermal_overload", re.compile(r"thermal|cpu.*overload", re.IGNORECASE)),
]


class IncidentTrigger:
    """Maintains a sliding log window and emits incident candidates."""

    def __init__(self, context_window_lines: int = 100) -> None:
        self._window: deque[str] = deque(maxlen=context_window_lines)

    def consume(self, line: str, timestamp: datetime, source: str) -> IncidentCandidate | None:
        self._window.append(line)

        for _, pattern in _PATTERN_RULES:
            if pattern.search(line):
                return IncidentCandidate(
                    timestamp=timestamp,
                    raw_log="\n".join(self._window),
                    source=source,
                )
        return None


def classify_hint(raw_log: str) -> str:
    for label, pattern in _PATTERN_RULES:
        if pattern.search(raw_log):
            return label
    return "unknown"


def any_triggered(lines: Iterable[str]) -> bool:
    for line in lines:
        for _, pattern in _PATTERN_RULES:
            if pattern.search(line):
                return True
    return False
