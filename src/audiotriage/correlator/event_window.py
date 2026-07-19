from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta
from typing import Any

from .types import SystemEvent

_PREDICATES = [
    '(subsystem == "com.apple.iokit.usb")',
    '(subsystem == "com.apple.iokit.thermal")',
    '(eventMessage CONTAINS[c] "wake" OR eventMessage CONTAINS[c] "sleep")',
    '(process == "logicpro" OR process == "Logic Pro")',
]


class SystemEventWindowQuery:
    def __init__(self, log_binary_path: str) -> None:
        self._log_binary_path = log_binary_path

    def query(self, incident_timestamp: datetime, window_seconds: int) -> list[SystemEvent]:
        start = (incident_timestamp - timedelta(seconds=window_seconds)).isoformat()
        end = (incident_timestamp + timedelta(seconds=window_seconds)).isoformat()
        predicate = " OR ".join(_PREDICATES)

        command = [
            self._log_binary_path,
            "show",
            "--style",
            "json",
            "--start",
            start,
            "--end",
            end,
            "--predicate",
            predicate,
        ]
        result = subprocess.run(  # noqa: S603
            command,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []

        events: list[SystemEvent] = []
        for line in result.stdout.splitlines():
            payload = line.strip()
            if not payload:
                continue
            try:
                record = json.loads(payload)
            except json.JSONDecodeError:
                continue
            if not isinstance(record, dict):
                continue
            event = _to_event(record)
            if event is not None:
                events.append(event)
        return events


def _to_event(record: dict[str, Any]) -> SystemEvent | None:
    timestamp_str = record.get("timestamp")
    message = record.get("eventMessage") or record.get("message")
    source = record.get("subsystem") or record.get("process") or "system"
    if not isinstance(timestamp_str, str) or not isinstance(message, str):
        return None

    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    except ValueError:
        return None

    return SystemEvent(timestamp=timestamp, source=str(source), message=message)
