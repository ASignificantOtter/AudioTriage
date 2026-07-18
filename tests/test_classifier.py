from datetime import datetime

from audiotriage.classifier.service import IncidentClassifier


def test_classifier_known_patterns() -> None:
    classifier = IncidentClassifier(confidence_threshold=0.7)
    now = datetime(2026, 1, 1)

    assert classifier.classify(timestamp=now, raw_log="coreaudiod underrun detected").category == "buffer_underrun"
    assert classifier.classify(timestamp=now, raw_log="USB device removed while active").category == "device_disconnect"
    assert classifier.classify(timestamp=now, raw_log="sample rate mismatch between apps").category == "sample_rate_mismatch"
    assert classifier.classify(timestamp=now, raw_log="coreaudiod restart completed").category == "driver_restart"
    assert classifier.classify(timestamp=now, raw_log="thermal pressure + cpu overload").category == "cpu_thermal_overload"


def test_classifier_low_confidence_falls_back_to_unknown() -> None:
    classifier = IncidentClassifier(confidence_threshold=0.7)
    result = classifier.classify(timestamp=datetime(2026, 1, 1), raw_log="minor unrelated line")

    assert result.category == "unknown"
