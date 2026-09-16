from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest


@pytest.fixture
def config_writer() -> Callable[[Path], tuple[Path, Path, Path]]:
    def _write_config(tmp_path: Path) -> tuple[Path, Path, Path]:
        db_path = tmp_path / "audiotriage.sqlite3"
        output_dir = tmp_path / "reports"
        config_path = tmp_path / "audiotriage.toml"
        config_path.write_text(
            f"""
[api]
llm_api_key = "test"

[paths]
log_binary_path = "/bin/echo"
system_profiler_path = "/bin/echo"
powermetrics_path = "/bin/echo"

[logs]
coreaudiod_log_predicate = "process == \\"coreaudiod\\""
usb_log_predicate = "subsystem == \\"com.apple.iokit.usb\\""

[thresholds]
correlation_window_seconds = 10
confidence_threshold = 0.7

[storage]
database_path = "{db_path}"
""".strip(),
            encoding="utf-8",
        )
        return config_path, db_path, output_dir

    return _write_config
