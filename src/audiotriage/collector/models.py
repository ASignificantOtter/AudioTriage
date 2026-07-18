from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class IncidentCandidate:
    timestamp: datetime
    raw_log: str
    source: str


@dataclass(slots=True)
class DeviceState:
    polled_at: datetime
    active_devices: list[str]
    sample_rate_hz: float | None
    buffer_size_frames: int | None


@dataclass(slots=True)
class SystemSample:
    sampled_at: datetime
    cpu_percent: float
    thermal_pressure: str | None
    cpu_temperature_c: float | None
