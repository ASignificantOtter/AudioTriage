from __future__ import annotations

from collections.abc import Iterator
import json
import subprocess


class UnifiedLogTailer:
    """Wrapper around `log stream` that yields structured log records."""

    def __init__(self, log_binary_path: str, predicate: str) -> None:
        self._command = [
            log_binary_path,
            "stream",
            "--style",
            "json",
            "--predicate",
            predicate,
            "--color",
            "none",
        ]

    def iter_records(self) -> Iterator[dict[str, object]]:
        process = subprocess.Popen(  # noqa: S603
            self._command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        if process.stdout is None:
            raise RuntimeError("log stream did not provide stdout")

        for line in process.stdout:
            payload = line.strip()
            if not payload:
                continue
            try:
                record = json.loads(payload)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                yield record


def coreaudiod_tailer(log_binary_path: str, predicate: str) -> UnifiedLogTailer:
    return UnifiedLogTailer(log_binary_path=log_binary_path, predicate=predicate)


def usb_tailer(log_binary_path: str, predicate: str) -> UnifiedLogTailer:
    return UnifiedLogTailer(log_binary_path=log_binary_path, predicate=predicate)
