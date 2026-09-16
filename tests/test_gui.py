from __future__ import annotations

from pathlib import Path

from audiotriage.gui import build_application


def test_build_application_offscreen(tmp_path: Path, monkeypatch) -> None:
    config_path, output_dir = _write_config(tmp_path)
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    app = build_application(config_path, output_dir=output_dir)
    window = app.property("audiotriage_window")

    assert window is not None
    window.close()
    app.processEvents()
    app.quit()


def _write_config(tmp_path: Path) -> tuple[Path, Path]:
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
    return config_path, output_dir
