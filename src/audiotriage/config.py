from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Settings:
    """Configuration loaded from TOML and environment overrides."""

    llm_api_key: str
    log_binary_path: str
    system_profiler_path: str
    powermetrics_path: str
    coreaudiod_log_predicate: str
    usb_log_predicate: str
    correlation_window_seconds: int
    confidence_threshold: float
    database_path: str


def _require_str(data: dict[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing or invalid string value for key '{key}'")
    return value


def _require_int(data: dict[str, object], key: str) -> int:
    value = data.get(key)
    if not isinstance(value, int):
        raise ValueError(f"Missing or invalid integer value for key '{key}'")
    return value


def _require_float(data: dict[str, object], key: str) -> float:
    value = data.get(key)
    if isinstance(value, int):
        return float(value)
    if not isinstance(value, float):
        raise ValueError(f"Missing or invalid float value for key '{key}'")
    return value


def load_settings(config_path: Path | str) -> Settings:
    """Load app settings from a TOML file and apply environment overrides."""
    config_file = Path(config_path)
    parsed = tomllib.loads(config_file.read_text(encoding="utf-8"))

    api = parsed.get("api", {})
    logs = parsed.get("logs", {})
    paths = parsed.get("paths", {})
    thresholds = parsed.get("thresholds", {})
    storage = parsed.get("storage", {})

    if not isinstance(api, dict) or not isinstance(logs, dict):
        raise ValueError("Invalid config format: [api] and [logs] tables are required")
    if not isinstance(paths, dict):
        raise ValueError("Invalid config format: [paths] table is required")
    if not isinstance(thresholds, dict) or not isinstance(storage, dict):
        raise ValueError("Invalid config format: [thresholds] and [storage] tables are required")

    llm_api_key = os.getenv("AUDIOTRIAGE_LLM_API_KEY", _require_str(api, "llm_api_key"))
    correlation_window_seconds = int(
        os.getenv(
            "AUDIOTRIAGE_CORRELATION_WINDOW_SECONDS",
            str(_require_int(thresholds, "correlation_window_seconds")),
        )
    )
    confidence_threshold = float(
        os.getenv(
            "AUDIOTRIAGE_CONFIDENCE_THRESHOLD",
            str(_require_float(thresholds, "confidence_threshold")),
        )
    )

    return Settings(
        llm_api_key=llm_api_key,
        log_binary_path=_require_str(paths, "log_binary_path"),
        system_profiler_path=_require_str(paths, "system_profiler_path"),
        powermetrics_path=_require_str(paths, "powermetrics_path"),
        coreaudiod_log_predicate=_require_str(logs, "coreaudiod_log_predicate"),
        usb_log_predicate=_require_str(logs, "usb_log_predicate"),
        correlation_window_seconds=correlation_window_seconds,
        confidence_threshold=confidence_threshold,
        database_path=_require_str(storage, "database_path"),
    )
