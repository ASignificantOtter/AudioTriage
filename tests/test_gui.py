from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from audiotriage.db import initialize_database
from audiotriage.gui import build_application
from audiotriage.services import AudioTriageServices


def test_build_application_offscreen(
    tmp_path: Path,
    monkeypatch,
    config_writer: Callable[[Path], tuple[Path, Path, Path]],
) -> None:
    config_path, db_path, output_dir = config_writer(tmp_path)
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
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
        connection.commit()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary-2026-09-09_to_2026-09-16.md").write_text("# Summary\n", encoding="utf-8")
    (output_dir / "summary-2026-09-09_to_2026-09-16.json").write_text("{}", encoding="utf-8")

    app = build_application(config_path, output_dir=output_dir)
    window = app.property("audiotriage_window")

    assert window is not None
    assert window._incident_table.rowCount() == 1
    assert window._summary_table.rowCount() == 1
    window.close()
    app.processEvents()
    app.quit()
