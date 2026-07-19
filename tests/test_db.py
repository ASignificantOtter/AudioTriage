import sqlite3
from pathlib import Path

from audiotriage.db import initialize_database


def test_initialize_database_creates_incidents_table(tmp_path: Path) -> None:
    db_path = tmp_path / "audiotriage.sqlite3"

    initialize_database(db_path)

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='incidents'"
        ).fetchone()

    assert row is not None
