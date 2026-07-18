from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime

from .prompt import INCIDENT_REPORT_TEMPLATE, SUMMARY_REPORT_TEMPLATE


@dataclass(slots=True)
class IncidentReport:
    markdown: str
    payload: dict[str, object]


@dataclass(slots=True)
class SummaryReport:
    markdown: str
    payload: dict[str, object]


class ReportWriter:
    def build_incident_report(
        self,
        *,
        timestamp: datetime,
        category: str,
        confidence: float,
        likely_cause: str,
        evidence: list[str],
        raw_context: str,
    ) -> IncidentReport:
        evidence_block = "\n".join(f"- {entry}" for entry in evidence) if evidence else "- None"
        markdown = INCIDENT_REPORT_TEMPLATE.format(
            timestamp=timestamp.isoformat(),
            category=category,
            confidence=confidence,
            likely_cause=likely_cause,
            evidence_block=evidence_block,
            raw_context=raw_context,
        )
        payload = {
            "timestamp": timestamp.isoformat(),
            "category": category,
            "confidence": confidence,
            "likely_cause": likely_cause,
            "evidence": evidence,
            "raw_context": raw_context,
        }
        return IncidentReport(markdown=markdown, payload=payload)

    def build_summary(
        self,
        *,
        since: datetime,
        until: datetime,
        incidents: list[dict[str, object]],
    ) -> SummaryReport:
        category_counts = Counter(str(item.get("class", "unknown")) for item in incidents)
        cause_counts = Counter(str(item.get("correlated_cause", "unknown")) for item in incidents)

        category_block = _counter_block(category_counts)
        cause_block = _counter_block(cause_counts)

        markdown = SUMMARY_REPORT_TEMPLATE.format(
            since=since.isoformat(),
            until=until.isoformat(),
            total=len(incidents),
            category_block=category_block,
            cause_block=cause_block,
        )

        payload = {
            "since": since.isoformat(),
            "until": until.isoformat(),
            "total": len(incidents),
            "categories": dict(category_counts),
            "causes": dict(cause_counts),
        }
        return SummaryReport(markdown=markdown, payload=payload)


def _counter_block(counter: Counter[str]) -> str:
    if not counter:
        return "- None"
    return "\n".join(f"- {key}: {value}" for key, value in counter.most_common())
