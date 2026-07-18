from __future__ import annotations

from pathlib import Path


def render_plist(program: str, working_directory: str, label: str) -> str:
    """Render a launchd plist payload for the collector service."""
    return f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">
<plist version=\"1.0\">
<dict>
    <key>Label</key>
    <string>{label}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{program}</string>
        <string>run</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{working_directory}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{working_directory}/var/collector.stdout.log</string>
    <key>StandardErrorPath</key>
    <string>{working_directory}/var/collector.stderr.log</string>
</dict>
</plist>
"""


def write_plist(destination: Path, *, program: str, working_directory: str, label: str) -> None:
    destination.write_text(
        render_plist(program=program, working_directory=working_directory, label=label),
        encoding="utf-8",
    )
