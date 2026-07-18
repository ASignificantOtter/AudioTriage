from __future__ import annotations

from dataclasses import dataclass

INCIDENT_CLASSES = {
    "buffer_underrun",
    "device_disconnect",
    "sample_rate_mismatch",
    "driver_restart",
    "cpu_thermal_overload",
    "unknown",
}


@dataclass(slots=True)
class ClassificationResult:
    category: str
    confidence: float
    reasoning: str

    def normalized(self) -> "ClassificationResult":
        category = self.category if self.category in INCIDENT_CLASSES else "unknown"
        confidence = min(max(self.confidence, 0.0), 1.0)
        return ClassificationResult(category=category, confidence=confidence, reasoning=self.reasoning)
