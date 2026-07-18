from __future__ import annotations

import sqlite3
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = PACKAGE_ROOT / "schema.sql"


def get_connection(database_path: Path | str) -> sqlite3.Connection:
    """Return a SQLite connection with row mapping enabled."""
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(database_path: Path | str) -> None:
    """Create the database file and incident schema if missing."""
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with get_connection(database_path) as connection:
        connection.executescript(schema_sql)
        connection.commit()
