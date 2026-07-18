from __future__ import annotations

from datetime import datetime, timezone
import json
from sqlite3 import Connection
import threading
from typing import Any

from .log_tailer import coreaudiod_tailer, usb_tailer
from .store import write_candidate
from .triggers import IncidentTrigger


class CollectorService:
    """Runs log tailers and writes incident candidates to SQLite."""

    def __init__(
        self,
        connection: Connection,
        log_binary_path: str,
        coreaudiod_predicate: str,
        usb_predicate: str,
    ) -> None:
        self._connection = connection
        self._coreaudiod = coreaudiod_tailer(log_binary_path, coreaudiod_predicate)
        self._usb = usb_tailer(log_binary_path, usb_predicate)
        self._core_trigger = IncidentTrigger()
        self._usb_trigger = IncidentTrigger()

    def process_record(self, source: str, record: dict[str, Any]) -> None:
        timestamp = _extract_timestamp(record)
        message = _extract_message(record)
        if message is None:
            return

        trigger = self._core_trigger if source == "coreaudiod" else self._usb_trigger
        candidate = trigger.consume(message, timestamp=timestamp, source=source)
        if candidate is None:
            return

        write_candidate(self._connection, candidate)
        self._connection.commit()

    def run_coreaudiod(self) -> None:
        for record in self._coreaudiod.iter_records():
            self.process_record("coreaudiod", record)

    def run_usb(self) -> None:
        for record in self._usb.iter_records():
            self.process_record("usb", record)

    def run_forever(self) -> None:
        threads = [
            threading.Thread(target=self.run_coreaudiod, daemon=True),
            threading.Thread(target=self.run_usb, daemon=True),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()


def _extract_timestamp(record: dict[str, Any]) -> datetime:
    value = record.get("timestamp") or record.get("eventTime")
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.now(tz=timezone.utc)


def _extract_message(record: dict[str, Any]) -> str | None:
    for key in ("eventMessage", "message", "composedMessage"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value

    payload = record.get("payload")
    if isinstance(payload, str) and payload.strip():
        return payload

    if isinstance(payload, dict):
        try:
            return json.dumps(payload)
        except TypeError:
            return None

    return None
