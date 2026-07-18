from __future__ import annotations

import json
from sqlite3 import Connection

from .models import IncidentCandidate
from .triggers import classify_hint


def write_candidate(connection: Connection, candidate: IncidentCandidate) -> None:
    """Persist a collector incident candidate into the incidents table."""
    raw_payload = {
        "source": candidate.source,
        "context": candidate.raw_log,
    }

    connection.execute(
        """
        INSERT INTO incidents (
            incident_timestamp,
            raw_log,
            class,
            confidence,
            correlated_cause,
            report_text
        ) VALUES (?, ?, ?, ?, NULL, NULL)
        """,
        (
            candidate.timestamp.isoformat(),
            json.dumps(raw_payload),
            classify_hint(candidate.raw_log),
            0.0,
        ),
    )
