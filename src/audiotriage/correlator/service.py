from __future__ import annotations

from datetime import datetime
from typing import Protocol

from .prompt import CORRELATOR_SYSTEM_PROMPT, CORRELATOR_TEMPLATE
from .types import CorrelationResult, SystemEvent


class LLMClient(Protocol):
    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, object]: ...


class IncidentCorrelator:
    def __init__(self, client: LLMClient | None = None) -> None:
        self._client = client

    def correlate(
        self,
        *,
        incident_timestamp: datetime,
        incident_category: str,
        incident_summary: str,
        events: list[SystemEvent],
    ) -> CorrelationResult:
        if not events:
            return CorrelationResult(
                likely_cause="no correlated system event found",
                evidence=[],
                no_correlated_event=True,
            )

        if self._client is None:
            first = events[0]
            return CorrelationResult(
                likely_cause=f"{first.source} event near incident",
                evidence=[f"{first.timestamp.isoformat()} {first.message}"],
            )

        event_lines = "\n".join(
            f"- {event.timestamp.isoformat()} [{event.source}] {event.message}" for event in events
        )
        user_prompt = CORRELATOR_TEMPLATE.format(
            category=incident_category,
            timestamp=incident_timestamp.isoformat(),
            incident_summary=incident_summary,
            event_lines=event_lines,
        )
        payload = self._client.complete_json(
            system_prompt=CORRELATOR_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        likely_cause = str(payload.get("likely_cause", "no correlated system event found"))
        evidence_payload = payload.get("evidence", [])
        evidence = (
            [str(item) for item in evidence_payload]
            if isinstance(evidence_payload, list)
            else []
        )
        no_correlated_event = bool(payload.get("no_correlated_event", False))
        return CorrelationResult(
            likely_cause=likely_cause,
            evidence=evidence,
            no_correlated_event=no_correlated_event,
        )
