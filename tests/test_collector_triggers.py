from datetime import UTC, datetime

from audiotriage.collector.triggers import IncidentTrigger, any_triggered, classify_hint


def test_incident_trigger_emits_candidate_for_buffer_underrun() -> None:
    trigger = IncidentTrigger(context_window_lines=4)
    timestamp = datetime.now(tz=UTC)

    candidate = trigger.consume(
        "coreaudiod: output buffer underrun detected",
        timestamp=timestamp,
        source="coreaudiod",
    )

    assert candidate is not None
    assert candidate.source == "coreaudiod"
    assert "underrun" in candidate.raw_log


def test_classify_hint_and_any_triggered() -> None:
    assert classify_hint("sample rate mismatch while switching interface") == "sample_rate_mismatch"
    assert any_triggered(["normal line", "device disconnect during session"])
