from datetime import datetime

from audiotriage.reporter.service import ReportWriter


def test_build_incident_report_contains_expected_fields() -> None:
    writer = ReportWriter()
    report = writer.build_incident_report(
        timestamp=datetime(2026, 1, 1),
        category="buffer_underrun",
        confidence=0.91,
        likely_cause="usb event",
        evidence=["2026-01-01T00:00:01 USB disconnected"],
        raw_context="underrun line",
    )

    assert "buffer_underrun" in report.markdown
    assert report.payload["likely_cause"] == "usb event"


def test_build_summary_rolls_up_categories() -> None:
    writer = ReportWriter()
    report = writer.build_summary(
        since=datetime(2026, 1, 1),
        until=datetime(2026, 1, 8),
        incidents=[
            {"class": "buffer_underrun", "correlated_cause": "usb"},
            {"class": "buffer_underrun", "correlated_cause": "usb"},
            {"class": "driver_restart", "correlated_cause": "unknown"},
        ],
    )

    assert report.payload["total"] == 3
    assert report.payload["categories"]["buffer_underrun"] == 2
