#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST_TEMPLATE="$ROOT_DIR/launchd/com.audiotriage.collector.plist.template"
PLIST_TARGET="$HOME/Library/LaunchAgents/com.audiotriage.collector.plist"
AUDIO_TRIAGE_BIN="${1:-$ROOT_DIR/.venv/bin/audiotriage}"

mkdir -p "$HOME/Library/LaunchAgents"
mkdir -p "$ROOT_DIR/var"

sed \
  -e "s|{{AUDIO_TRIAGE_BIN}}|$AUDIO_TRIAGE_BIN|g" \
  -e "s|{{AUDIO_TRIAGE_ROOT}}|$ROOT_DIR|g" \
  "$PLIST_TEMPLATE" > "$PLIST_TARGET"

launchctl unload "$PLIST_TARGET" >/dev/null 2>&1 || true
launchctl load "$PLIST_TARGET"

printf 'Installed and loaded %s\n' "$PLIST_TARGET"
