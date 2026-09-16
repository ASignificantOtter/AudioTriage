from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

from audiotriage.db import initialize_database
from audiotriage.services import AudioTriageServices


def test_services_list_incidents_and_dashboard(
    tmp_path: Path,
    config_writer: Callable[[Path], tuple[Path, Path, Path]],
) -> None:
    config_path, db_path, output_dir = config_writer(tmp_path)
    initialize_database(db_path)

    services = AudioTriageServices(config_path=config_path, output_dir=output_dir)
    with services._connect() as connection:
        connection.execute(
            """
            INSERT INTO incidents (
                incident_timestamp,
                raw_log,
                class,
                confidence,
                correlated_cause,
                report_text
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "2026-09-16T12:00:00",
                '{"context": "USB reset during playback"}',
                "device_disconnect",
                0.92,
                "USB reset",
                "Report text",
            ),
        )
        connection.execute(
            """
            INSERT INTO incidents (
                incident_timestamp,
                raw_log,
                class,
                confidence,
                correlated_cause,
                report_text
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "2026-09-15T12:00:00",
                '{"context": "Buffer underrun"}',
                "buffer_underrun",
                0.81,
                "CPU pressure",
                None,
            ),
        )
        connection.commit()

    incidents = services.list_incidents()
    assert [item.category for item in incidents] == ["device_disconnect", "buffer_underrun"]

    detail = services.get_incident(incidents[0].incident_id)
    assert detail is not None
    assert detail.raw_context == "USB reset during playback"

    dashboard = services.dashboard_data()
    assert dashboard.latest_incident is not None
    top_categories = dict(dashboard.top_categories)
    assert top_categories["device_disconnect"] == 1
    assert top_categories["buffer_underrun"] == 1


def test_validate_settings_reports_missing_paths(tmp_path: Path) -> None:
    db_path = tmp_path / "db.sqlite3"
    config_path = tmp_path / "bad.toml"
    config_path.write_text(
        f"""
[api]
llm_api_key = "test"

[paths]
log_binary_path = "{tmp_path / "missing-log"}"
system_profiler_path = "{tmp_path / "missing-sp"}"
powermetrics_path = "{tmp_path / "missing-power"}"

[logs]
coreaudiod_log_predicate = "process == \\"coreaudiod\\""
usb_log_predicate = "subsystem == \\"com.apple.iokit.usb\\""

[thresholds]
correlation_window_seconds = 0
confidence_threshold = 1.5

[storage]
database_path = "{db_path}"
""".strip(),
        encoding="utf-8",
    )

    output_dir = tmp_path / "var" / "reports"
    pid_path = tmp_path / "var" / "collector.pid"
    result = AudioTriageServices(
        config_path,
        output_dir=output_dir,
        collector_pid_path=pid_path,
    ).validate_settings()

    assert result.valid is False
    assert any("Missing required path" in message for message in result.errors)
    assert any(
        "confidence_threshold must be between 0.0 and 1.0" == message
        for message in result.errors
    )
    assert not output_dir.exists()
    assert not pid_path.parent.exists()


def test_list_summary_files_groups_markdown_and_json(
    tmp_path: Path,
    config_writer: Callable[[Path], tuple[Path, Path, Path]],
) -> None:
    config_path, _, output_dir = config_writer(tmp_path)
    services = AudioTriageServices(config_path=config_path, output_dir=output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary-2026-09-01_to_2026-09-07.md").write_text("# Summary\n", encoding="utf-8")
    (output_dir / "summary-2026-09-01_to_2026-09-07.json").write_text("{}", encoding="utf-8")

    summaries = services.list_summary_files()

    assert len(summaries) == 1
    assert summaries[0].markdown_path is not None
    assert summaries[0].json_path is not None


def test_latest_report_paths_returns_newest_pair(
    tmp_path: Path,
    config_writer: Callable[[Path], tuple[Path, Path, Path]],
) -> None:
    config_path, _, output_dir = config_writer(tmp_path)
    services = AudioTriageServices(config_path=config_path, output_dir=output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "incident-older.md").write_text("old", encoding="utf-8")
    (output_dir / "incident-newer.md").write_text("new", encoding="utf-8")
    (output_dir / "incident-newer.json").write_text("{}", encoding="utf-8")

    markdown_path, json_path = services.latest_report_paths()

    assert markdown_path is not None
    assert markdown_path.name == "incident-newer.md"
    assert json_path is not None
    assert json_path.name == "incident-newer.json"


def test_collector_status_uses_pid_file(
    tmp_path: Path,
    config_writer: Callable[[Path], tuple[Path, Path, Path]],
) -> None:
    config_path, _, _ = config_writer(tmp_path)
    pid_path = tmp_path / "collector.pid"
    pid_path.write_text(str(_current_pid()), encoding="utf-8")

    status = AudioTriageServices(
        config_path=config_path,
        collector_pid_path=pid_path,
    ).collector_status()

    assert status.running is True
    assert status.pid == _current_pid()


def test_ensure_runtime_directories_creates_output_and_pid_parents(
    tmp_path: Path,
    config_writer: Callable[[Path], tuple[Path, Path, Path]],
) -> None:
    config_path, _, _ = config_writer(tmp_path)
    output_dir = tmp_path / "nested" / "reports"
    pid_path = tmp_path / "runtime" / "collector.pid"

    services = AudioTriageServices(
        config_path=config_path,
        output_dir=output_dir,
        collector_pid_path=pid_path,
    )
    services.ensure_runtime_directories()

    assert output_dir.exists()
    assert pid_path.parent.exists()


def _current_pid() -> int:
    return os.getpid()
