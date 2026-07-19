from datetime import datetime

import pytest

from audiotriage.classifier.service import IncidentClassifier


@pytest.mark.parametrize(
    ("raw_log", "expected"),
    [
        pytest.param("coreaudiod underrun detected", "buffer_underrun", id="buffer-underrun"),
        pytest.param(
            "USB device removed while active",
            "device_disconnect",
            id="device-disconnect",
        ),
        pytest.param("sample rate mismatch between apps", "sample_rate_mismatch", id="sample-rate"),
        pytest.param("coreaudiod restart completed", "driver_restart", id="driver-restart"),
        pytest.param("thermal pressure + cpu overload", "cpu_thermal_overload", id="cpu-thermal"),
    ],
)
def test_classifier_known_patterns(raw_log: str, expected: str) -> None:
    classifier = IncidentClassifier(confidence_threshold=0.7)
    now = datetime(2026, 1, 1)

    assert classifier.classify(timestamp=now, raw_log=raw_log).category == expected


def test_classifier_low_confidence_falls_back_to_unknown() -> None:
    classifier = IncidentClassifier(confidence_threshold=0.7)
    result = classifier.classify(timestamp=datetime(2026, 1, 1), raw_log="minor unrelated line")

    assert result.category == "unknown"
