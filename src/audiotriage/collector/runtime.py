from __future__ import annotations

from pathlib import Path

from audiotriage.config import load_settings
from audiotriage.db import get_connection, initialize_database

from .service import CollectorService


def start_collector(config_path: Path | str) -> None:
    """Initialize dependencies and start collector loops."""
    settings = load_settings(config_path)
    initialize_database(settings.database_path)

    with get_connection(settings.database_path) as connection:
        service = CollectorService(
            connection=connection,
            log_binary_path=settings.log_binary_path,
            coreaudiod_predicate=settings.coreaudiod_log_predicate,
            usb_predicate=settings.usb_log_predicate,
        )
        service.run_forever()
