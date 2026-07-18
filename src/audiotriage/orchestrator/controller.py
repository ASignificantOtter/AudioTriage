from __future__ import annotations

from datetime import datetime, timedelta
import json
from pathlib import Path
from sqlite3 import Connection

from audiotriage.classifier import IncidentClassifier
from audiotriage.correlator import IncidentCorrelator, SystemEventWindowQuery
from audiotriage.correlator.types import SystemEvent
from audiotriage.reporter.output import write_incident_report, write_summary_report
from audiotriage.reporter.service import ReportWriter

from .retry import with_retries


class PipelineController:
    def __init__(
        self,
        *,
        connection: Connection,
        classifier: IncidentClassifier,
        correlator: IncidentCorrelator,
        event_query: SystemEventWindowQuery,
        report_writer: ReportWriter,
        correlation_window_seconds: int,
    ) -> None:
        self._connection = connection
        self._classifier = classifier
        self._correlator = correlator
        self._event_query = event_query
        self._report_writer = report_writer
        self._correlation_window_seconds = correlation_window_seconds

    def process_unreported(self, output_dir: str, limit: int = 50, since: datetime | None = None) -> int:
        if since is None:
            rows = self._connection.execute(
                """
                SELECT id, incident_timestamp, raw_log
                FROM incidents
                WHERE report_text IS NULL
                ORDER BY incident_timestamp ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        else:
            rows = self._connection.execute(
                """
                SELECT id, incident_timestamp, raw_log
                FROM incidents
                WHERE report_text IS NULL AND incident_timestamp >= ?
                ORDER BY incident_timestamp ASC
                LIMIT ?
                """,
                (since.isoformat(), limit),
            ).fetchall()

        processed = 0
        for row in rows:
            incident_id = int(row[0])
            timestamp = datetime.fromisoformat(str(row[1]))
            raw_payload = _parse_raw_payload(str(row[2]))
            raw_context = str(raw_payload.get("context", ""))

            classification = with_retries(
                lambda: self._classifier.classify(timestamp=timestamp, raw_log=raw_context)
            )
            events = self._event_query.query(timestamp, self._correlation_window_seconds)
            correlation = with_retries(
                lambda: self._correlator.correlate(
                    incident_timestamp=timestamp,
                    incident_category=classification.category,
                    incident_summary=raw_context,
                    events=events,
                )
            )

            report = with_retries(
                lambda: self._report_writer.build_incident_report(
                    timestamp=timestamp,
                    category=classification.category,
                    confidence=classification.confidence,
                    likely_cause=correlation.likely_cause,
                    evidence=correlation.evidence,
                    raw_context=raw_context,
                )
            )
            write_incident_report(report, output_dir=Path(output_dir))

            self._connection.execute(
                """
                UPDATE incidents
                SET class = ?, confidence = ?, correlated_cause = ?, report_text = ?
                WHERE id = ?
                """,
                (
                    classification.category,
                    classification.confidence,
                    correlation.likely_cause,
                    report.markdown,
                    incident_id,
                ),
            )
            self._connection.commit()
            processed += 1

        return processed

    def build_summary(self, output_dir: str, since: datetime, until: datetime) -> tuple[str, str]:
        rows = self._connection.execute(
            """
            SELECT class, correlated_cause
            FROM incidents
            WHERE incident_timestamp >= ? AND incident_timestamp <= ?
            ORDER BY incident_timestamp ASC
            """,
            (since.isoformat(), until.isoformat()),
        ).fetchall()

        incidents = [
            {"class": str(row[0]), "correlated_cause": str(row[1] or "unknown")}
            for row in rows
        ]
        summary = self._report_writer.build_summary(since=since, until=until, incidents=incidents)
        md_path, json_path = write_summary_report(
            summary,
            output_dir=Path(output_dir),
            label=f"{since.date()}_to_{until.date()}",
        )
        return str(md_path), str(json_path)


def _parse_raw_payload(raw_log: str) -> dict[str, object]:
    try:
        payload = json.loads(raw_log)
    except json.JSONDecodeError:
        return {"context": raw_log}
    if isinstance(payload, dict):
        return payload
    return {"context": raw_log}


def default_since(days: int = 7) -> datetime:
    return datetime.now() - timedelta(days=days)


def empty_events() -> list[SystemEvent]:
    return []
