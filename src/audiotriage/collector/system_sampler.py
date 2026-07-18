from __future__ import annotations

from datetime import datetime, timezone
import re
import subprocess

import psutil

from .models import SystemSample

_TEMPERATURE_PATTERN = re.compile(r"CPU die temperature:\s*([0-9]+(?:\.[0-9]+)?)")


class SystemSampler:
    """Collects CPU usage and best-effort thermal signals."""

    def __init__(self, powermetrics_path: str) -> None:
        self._powermetrics_path = powermetrics_path

    def sample(self) -> SystemSample:
        cpu_percent = psutil.cpu_percent(interval=0.2)
        cpu_temperature_c = self._try_powermetrics_temperature()

        return SystemSample(
            sampled_at=datetime.now(tz=timezone.utc),
            cpu_percent=cpu_percent,
            thermal_pressure=None,
            cpu_temperature_c=cpu_temperature_c,
        )

    def _try_powermetrics_temperature(self) -> float | None:
        result = subprocess.run(  # noqa: S603
            [
                self._powermetrics_path,
                "--samplers",
                "smc",
                "-n",
                "1",
                "-i",
                "1000",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return None

        match = _TEMPERATURE_PATTERN.search(result.stdout)
        if not match:
            return None

        try:
            return float(match.group(1))
        except ValueError:
            return None
