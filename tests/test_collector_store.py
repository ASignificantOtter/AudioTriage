import json
import sqlite3
from datetime import datetime
from pathlib import Path

from audiotriage.collector.models import IncidentCandidate
from audiotriage.collector.store import write_candidate
from audiotriage.db import initialize_database


def test_write_candidate_persists_row(tmp_path: Path) -> None:
    db_path = tmp_path / "audiotriage.sqlite3"
    initialize_database(db_path)

    candidate = IncidentCandidate(
        timestamp=datetime(2026, 1, 1),
        raw_log="device disconnect while active",
        source="usb",
    )

    with sqlite3.connect(db_path) as connection:
        write_candidate(connection, candidate)
        connection.commit()
        row = connection.execute(
            "SELECT incident_timestamp, raw_log, class, confidence FROM incidents"
        ).fetchone()

    assert row is not None
    assert row[0].startswith("2026-01-01")
    payload = json.loads(row[1])
    assert payload["source"] == "usb"
    assert row[2] == "device_disconnect"
    assert row[3] == 0.0
