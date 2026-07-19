from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime

from .models import DeviceState


class CoreAudioDevicePoller:
    """Best-effort poller using system_profiler SPAudioDataType JSON output."""

    def __init__(self, system_profiler_path: str) -> None:
        self._system_profiler_path = system_profiler_path

    def poll(self) -> DeviceState:
        command = [self._system_profiler_path, "SPAudioDataType", "-json"]
        result = subprocess.run(  # noqa: S603
            command,
            check=False,
            capture_output=True,
            text=True,
        )

        active_devices: list[str] = []
        sample_rate_hz: float | None = None
        buffer_size_frames: int | None = None

        if result.returncode == 0 and result.stdout:
            try:
                payload = json.loads(result.stdout)
            except json.JSONDecodeError:
                payload = {}
            devices = payload.get("SPAudioDataType", []) if isinstance(payload, dict) else []
            if isinstance(devices, list):
                for item in devices:
                    if not isinstance(item, dict):
                        continue
                    name = item.get("_name")
                    if isinstance(name, str):
                        active_devices.append(name)

                    # system_profiler sample rates may appear as "44.1 kHz".
                    value = item.get("coreaudio_default_audio_output_device_sample_rate")
                    if isinstance(value, str) and "kHz" in value and sample_rate_hz is None:
                        khz = value.lower().replace("khz", "").strip()
                        try:
                            sample_rate_hz = float(khz) * 1000.0
                        except ValueError:
                            sample_rate_hz = None

                    if buffer_size_frames is None:
                        buffer_size_frames = _extract_buffer_size(item)

        return DeviceState(
            polled_at=datetime.now(tz=UTC),
            active_devices=active_devices,
            sample_rate_hz=sample_rate_hz,
            buffer_size_frames=buffer_size_frames,
        )


def _extract_buffer_size(device: dict[str, object]) -> int | None:
    for key, value in device.items():
        if "buffer" not in key.lower():
            continue
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            digits = "".join(ch for ch in value if ch.isdigit())
            if digits:
                try:
                    return int(digits)
                except ValueError:
                    return None
    return None
