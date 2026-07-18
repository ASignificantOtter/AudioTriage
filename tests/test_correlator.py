from datetime import datetime, timezone

from audiotriage.correlator.service import IncidentCorrelator
from audiotriage.correlator.types import SystemEvent


def test_correlator_returns_no_event_message() -> None:
    correlator = IncidentCorrelator()
    result = correlator.correlate(
        incident_timestamp=datetime.now(tz=timezone.utc),
        incident_category="buffer_underrun",
        incident_summary="Underrun while recording",
        events=[],
    )

    assert result.no_correlated_event is True
    assert result.likely_cause == "no correlated system event found"


def test_correlator_uses_first_event_in_heuristic_mode() -> None:
    correlator = IncidentCorrelator()
    event = SystemEvent(
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        source="com.apple.iokit.usb",
        message="USB device disconnected",
    )
    result = correlator.correlate(
        incident_timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        incident_category="device_disconnect",
        incident_summary="Interface vanished",
        events=[event],
    )

    assert result.no_correlated_event is False
    assert "usb" in result.likely_cause.lower()
