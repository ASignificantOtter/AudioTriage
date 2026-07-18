from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Protocol

from .prompt import CLASSIFIER_SYSTEM_PROMPT, INCIDENT_TEMPLATE
from .types import ClassificationResult


class LLMClient(Protocol):
    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, object]: ...


class IncidentClassifier:
    def __init__(self, confidence_threshold: float, client: LLMClient | None = None) -> None:
        self._confidence_threshold = confidence_threshold
        self._client = client

    def classify(self, *, timestamp: datetime, raw_log: str) -> ClassificationResult:
        if self._client is None:
            result = self._heuristic_classify(raw_log)
        else:
            user_prompt = INCIDENT_TEMPLATE.format(timestamp=timestamp.isoformat(), raw_log=raw_log)
            payload = self._client.complete_json(
                system_prompt=CLASSIFIER_SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )
            result = ClassificationResult(
                category=str(payload.get("category", "unknown")),
                confidence=float(payload.get("confidence", 0.0)),
                reasoning=str(payload.get("reasoning", "No reasoning provided.")),
            ).normalized()

        if result.confidence < self._confidence_threshold:
            return ClassificationResult(
                category="unknown",
                confidence=result.confidence,
                reasoning=result.reasoning,
            )
        return result

    def _heuristic_classify(self, raw_log: str) -> ClassificationResult:
        lowered = raw_log.lower()
        rules = [
            ("cpu_thermal_overload", ["thermal pressure", "cpu overload", "throttl", "thermal"]),
            ("buffer_underrun", ["buffer underrun", "buffer overload", "i/o cycle slipped", "underrun"]),
            ("device_disconnect", ["device removed", "disconnect", "usb detach"]),
            ("sample_rate_mismatch", ["sample rate mismatch", "clock mismatch"]),
            ("driver_restart", ["coreaudiod restart", "coreaudiod relaunch", "driver restart"]),
        ]
        for category, tokens in rules:
            if any(token in lowered for token in tokens):
                return ClassificationResult(
                    category=category,
                    confidence=0.85,
                    reasoning=f"Matched heuristic tokens for {category}.",
                )

        return ClassificationResult(category="unknown", confidence=0.4, reasoning="No clear signal.")


def result_to_dict(result: ClassificationResult) -> dict[str, object]:
    return asdict(result)
