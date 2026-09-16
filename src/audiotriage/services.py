from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import webbrowser
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from sqlite3 import Connection

from audiotriage.classifier import IncidentClassifier
from audiotriage.collector import start_collector
from audiotriage.config import Settings, load_settings
from audiotriage.correlator import IncidentCorrelator, SystemEventWindowQuery
from audiotriage.db import get_connection, initialize_database
from audiotriage.orchestrator.controller import PipelineController
from audiotriage.reporter.service import ReportWriter


@dataclass(slots=True)
class CollectorStatus:
    running: bool
    message: str
    pid: int | None
    pid_file: Path
    last_incident_timestamp: str | None


@dataclass(slots=True)
class IncidentListItem:
    incident_id: int
    incident_timestamp: str
    category: str
    confidence: float
    correlated_cause: str | None
    has_report: bool


@dataclass(slots=True)
class IncidentDetail:
    incident_id: int
    incident_timestamp: str
    category: str
    confidence: float
    correlated_cause: str | None
    raw_context: str
    report_text: str | None
    created_at: str


@dataclass(slots=True)
class SummaryFile:
    label: str
    markdown_path: Path | None
    json_path: Path | None
    updated_at: str | None


@dataclass(slots=True)
class SettingsValidationResult:
    valid: bool
    settings: Settings | None
    errors: list[str]
    details: list[str]


@dataclass(slots=True)
class DashboardData:
    collector_status: CollectorStatus
    incidents_last_24_hours: int
    incidents_last_7_days: int
    top_categories: list[tuple[str, int]]
    top_causes: list[tuple[str, int]]
    latest_incident: IncidentListItem | None


class AudioTriageServices:
    def __init__(
        self,
        config_path: Path | str,
        *,
        output_dir: Path | str = "var/reports",
        collector_pid_path: Path | str = "var/collector.pid",
    ) -> None:
        self._config_path = Path(config_path)
        self._output_dir = Path(output_dir)
        self._collector_pid_path = Path(collector_pid_path)

    @property
    def config_path(self) -> Path:
        return self._config_path

    @property
    def output_dir(self) -> Path:
        return self._output_dir

    @property
    def collector_pid_path(self) -> Path:
        return self._collector_pid_path

    def load_current_settings(self) -> Settings:
        return load_settings(self._config_path)

    def validate_settings(self) -> SettingsValidationResult:
        errors: list[str] = []
        details: list[str] = []
        if not self._config_path.exists():
            return SettingsValidationResult(
                valid=False,
                settings=None,
                errors=[f"Config file does not exist: {self._config_path}"],
                details=[],
            )

        try:
            settings = self.load_current_settings()
        except (OSError, ValueError) as exc:
            return SettingsValidationResult(
                valid=False,
                settings=None,
                errors=[str(exc)],
                details=[],
            )

        tool_paths = {
            "log_binary_path": settings.log_binary_path,
            "system_profiler_path": settings.system_profiler_path,
            "powermetrics_path": settings.powermetrics_path,
        }
        for label, raw_path in tool_paths.items():
            if not Path(raw_path).exists():
                errors.append(f"Missing required path for {label}: {raw_path}")

        if settings.correlation_window_seconds <= 0:
            errors.append("correlation_window_seconds must be greater than zero")
        if not 0.0 <= settings.confidence_threshold <= 1.0:
            errors.append("confidence_threshold must be between 0.0 and 1.0")

        database_parent = Path(settings.database_path).parent
        if database_parent != Path() and not database_parent.exists():
            errors.append(f"Database parent directory does not exist: {database_parent}")

        details.append(f"Database path: {settings.database_path}")
        details.append(f"Report output directory: {self._output_dir}")
        return SettingsValidationResult(
            valid=not errors,
            settings=settings,
            errors=errors,
            details=details,
        )

    def _connect(self) -> Connection:
        settings = self.load_current_settings()
        self.ensure_runtime_directories()
        initialize_database(settings.database_path)
        return get_connection(settings.database_path)

    def ensure_runtime_directories(self) -> None:
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._collector_pid_path.parent.mkdir(parents=True, exist_ok=True)

    def run_collector_foreground(self) -> None:
        start_collector(self._config_path)

    def collector_status(self) -> CollectorStatus:
        pid = _read_pid(self._collector_pid_path)
        running = pid is not None and _pid_exists(pid)
        if pid is not None and not running:
            _remove_file_if_exists(self._collector_pid_path)
            pid = None

        last_incident_timestamp: str | None = None
        try:
            with self._connect() as connection:
                row = connection.execute(
                    """
                    SELECT incident_timestamp
                    FROM incidents
                    ORDER BY incident_timestamp DESC
                    LIMIT 1
                    """
                ).fetchone()
                if row is not None:
                    last_incident_timestamp = str(row[0])
        except (OSError, ValueError):
            last_incident_timestamp = None

        if running:
            message = f"Collector running (PID {pid})"
        else:
            message = "No managed collector process detected"

        return CollectorStatus(
            running=running,
            message=message,
            pid=pid,
            pid_file=self._collector_pid_path,
            last_incident_timestamp=last_incident_timestamp,
        )

    def start_collector_background(self) -> CollectorStatus:
        status = self.collector_status()
        if status.running:
            return status

        self._collector_pid_path.parent.mkdir(parents=True, exist_ok=True)
        log_path = self._collector_pid_path.with_suffix(".log")
        command = [
            sys.executable,
            "-m",
            "audiotriage.cli",
            "--config",
            str(self._config_path),
            "run",
        ]
        with log_path.open("a", encoding="utf-8") as log_handle:
            process = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                cwd=Path.cwd(),
            )
        self._collector_pid_path.write_text(str(process.pid), encoding="utf-8")
        return self.collector_status()

    def stop_collector_background(self) -> CollectorStatus:
        pid = _read_pid(self._collector_pid_path)
        if pid is None:
            return self.collector_status()
        if _pid_exists(pid):
            os.kill(pid, signal.SIGTERM)
        _remove_file_if_exists(self._collector_pid_path)
        return self.collector_status()

    def list_incidents(
        self,
        *,
        limit: int = 200,
        category: str | None = None,
        sort_by: str = "incident_timestamp",
        descending: bool = True,
    ) -> list[IncidentListItem]:
        sort_column = {
            "incident_timestamp": "incident_timestamp",
            "category": "class",
            "confidence": "confidence",
        }.get(sort_by, "incident_timestamp")
        sort_direction = "DESC" if descending else "ASC"
        query = """
            SELECT id, incident_timestamp, class, confidence, correlated_cause, report_text
            FROM incidents
        """
        params: tuple[object, ...]
        if category:
            query += " WHERE class = ?"
            params = (category, limit)
        else:
            params = (limit,)
        query += f" ORDER BY {sort_column} {sort_direction} LIMIT ?"

        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()

        return [
            IncidentListItem(
                incident_id=int(row[0]),
                incident_timestamp=str(row[1]),
                category=str(row[2]),
                confidence=float(row[3]),
                correlated_cause=str(row[4]) if row[4] is not None else None,
                has_report=row[5] is not None,
            )
            for row in rows
        ]

    def get_incident(self, incident_id: int) -> IncidentDetail | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    incident_timestamp,
                    class,
                    confidence,
                    correlated_cause,
                    raw_log,
                    report_text,
                    created_at
                FROM incidents
                WHERE id = ?
                """,
                (incident_id,),
            ).fetchone()
        if row is None:
            return None

        raw_payload = _parse_raw_log_payload(str(row[5]))
        return IncidentDetail(
            incident_id=int(row[0]),
            incident_timestamp=str(row[1]),
            category=str(row[2]),
            confidence=float(row[3]),
            correlated_cause=str(row[4]) if row[4] is not None else None,
            raw_context=str(raw_payload.get("context", "")),
            report_text=str(row[6]) if row[6] is not None else None,
            created_at=str(row[7]),
        )

    def list_summary_files(self) -> list[SummaryFile]:
        self._output_dir.mkdir(parents=True, exist_ok=True)
        grouped: dict[str, SummaryFile] = {}
        for path in sorted(self._output_dir.glob("summary-*.*")):
            if path.suffix not in {".md", ".json"}:
                continue
            label = path.stem.removeprefix("summary-")
            item = grouped.get(label)
            if item is None:
                item = SummaryFile(label=label, markdown_path=None, json_path=None, updated_at=None)
                grouped[label] = item
            if path.suffix == ".md":
                item.markdown_path = path
            else:
                item.json_path = path
            updated_at = datetime.fromtimestamp(path.stat().st_mtime).isoformat(
                timespec="seconds"
            )
            if item.updated_at is None:
                item.updated_at = updated_at
            else:
                item.updated_at = max(item.updated_at, updated_at)

        return sorted(grouped.values(), key=lambda item: item.updated_at or "", reverse=True)

    def latest_report_paths(self) -> tuple[Path | None, Path | None]:
        markdown_path = self._latest_output_path("incident-", ".md")
        json_path = self._latest_output_path("incident-", ".json")
        return markdown_path, json_path

    def process_unreported(self, *, since: datetime | None = None) -> int:
        with self._connect() as connection:
            controller = self._build_controller(connection)
            return controller.process_unreported(output_dir=str(self._output_dir), since=since)

    def generate_summary(self, *, since: datetime, until: datetime) -> tuple[Path, Path]:
        with self._connect() as connection:
            controller = self._build_controller(connection)
            md_path, json_path = controller.build_summary(
                output_dir=str(self._output_dir),
                since=since,
                until=until,
            )
        return Path(md_path), Path(json_path)

    def dashboard_data(self) -> DashboardData:
        latest_incident = self.list_incidents(limit=1)
        with self._connect() as connection:
            recent_24_hours = self._count_since(connection, timedelta(hours=24))
            recent_7_days = self._count_since(connection, timedelta(days=7))
            category_counts = Counter(
                {
                    str(row[0]): int(row[1])
                    for row in connection.execute(
                        """
                        SELECT class, COUNT(*)
                        FROM incidents
                        GROUP BY class
                        ORDER BY COUNT(*) DESC, class ASC
                        LIMIT 5
                        """
                    ).fetchall()
                }
            )
            cause_counts = Counter(
                {
                    str(row[0] or "unknown"): int(row[1])
                    for row in connection.execute(
                        """
                        SELECT COALESCE(correlated_cause, 'unknown'), COUNT(*)
                        FROM incidents
                        GROUP BY COALESCE(correlated_cause, 'unknown')
                        ORDER BY COUNT(*) DESC, COALESCE(correlated_cause, 'unknown') ASC
                        LIMIT 5
                        """
                    ).fetchall()
                }
            )

        return DashboardData(
            collector_status=self.collector_status(),
            incidents_last_24_hours=recent_24_hours,
            incidents_last_7_days=recent_7_days,
            top_categories=category_counts.most_common(5),
            top_causes=cause_counts.most_common(5),
            latest_incident=latest_incident[0] if latest_incident else None,
        )

    def open_path(self, path: Path) -> bool:
        if not path.exists():
            return False
        if sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
            return True
        return webbrowser.open(path.resolve().as_uri())

    def _build_controller(self, connection: Connection) -> PipelineController:
        settings = self.load_current_settings()
        return PipelineController(
            connection=connection,
            classifier=IncidentClassifier(confidence_threshold=settings.confidence_threshold),
            correlator=IncidentCorrelator(),
            event_query=SystemEventWindowQuery(settings.log_binary_path),
            report_writer=ReportWriter(),
            correlation_window_seconds=settings.correlation_window_seconds,
        )

    def _latest_output_path(self, prefix: str, suffix: str) -> Path | None:
        self._output_dir.mkdir(parents=True, exist_ok=True)
        candidates = sorted(self._output_dir.glob(f"{prefix}*{suffix}"))
        if not candidates:
            return None
        return max(candidates, key=lambda path: path.stat().st_mtime)

    def _count_since(self, connection: Connection, window: timedelta) -> int:
        threshold = (datetime.now() - window).isoformat()
        row = connection.execute(
            """
            SELECT COUNT(*)
            FROM incidents
            WHERE incident_timestamp >= ?
            """,
            (threshold,),
        ).fetchone()
        return int(row[0]) if row is not None else 0


def _read_pid(pid_path: Path) -> int | None:
    if not pid_path.exists():
        return None
    try:
        return int(pid_path.read_text(encoding="utf-8").strip())
    except ValueError:
        return None


def _pid_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _remove_file_if_exists(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        return


def _parse_raw_log_payload(raw_log: str) -> dict[str, object]:
    try:
        payload = json.loads(raw_log)
    except json.JSONDecodeError:
        return {"context": raw_log}
    if isinstance(payload, dict):
        return payload
    return {"context": raw_log}
