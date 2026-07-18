from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path

from .service import IncidentReport, SummaryReport


def write_incident_report(report: IncidentReport, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    md_path = output_dir / f"incident-{stamp}.md"
    json_path = output_dir / f"incident-{stamp}.json"
    md_path.write_text(report.markdown + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(report.payload, indent=2) + "\n", encoding="utf-8")
    return md_path, json_path


def write_summary_report(report: SummaryReport, output_dir: Path, label: str) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    md_path = output_dir / f"summary-{label}.md"
    json_path = output_dir / f"summary-{label}.json"
    md_path.write_text(report.markdown + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(report.payload, indent=2) + "\n", encoding="utf-8")
    return md_path, json_path
