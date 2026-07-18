from pathlib import Path

from audiotriage.config import load_settings


def test_load_settings_from_example_config() -> None:
    settings = load_settings(Path("config/audiotriage.example.toml"))

    assert settings.log_binary_path == "/usr/bin/log"
    assert settings.system_profiler_path == "/usr/sbin/system_profiler"
    assert settings.powermetrics_path == "/usr/bin/powermetrics"
    assert settings.coreaudiod_log_predicate == 'process == "coreaudiod"'
    assert settings.usb_log_predicate == 'subsystem == "com.apple.iokit.usb"'
    assert settings.correlation_window_seconds == 10
    assert settings.confidence_threshold == 0.70
