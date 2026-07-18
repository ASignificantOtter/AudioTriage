# Proposal: AudioTriage

## Why

Audio dropouts, glitches, and hardware disconnects during Logic Pro sessions
are hard to diagnose after the fact. By the time a musician notices a
buffer underrun or a dropped audio interface, the symptom is gone and the
underlying cause (driver restart, sample rate mismatch, USB power event,
thermal throttling, another app stealing the CoreAudio device) is buried in
system logs the average user never looks at.

**AudioTriage** is a multi-agent pipeline that watches macOS system logs,
CoreAudio state, and Logic Pro's own performance data, detects audio
incidents as they happen, and produces a plain-English root-cause report —
the same diagnostic process used professionally for hardware audio
certification (Klippel / Audio Precision / Head Acoustics workflows),
applied to a personal studio setup.

## What Changes

- Add a **Collector** component that taps macOS unified logging
  (`coreaudiod`, `logind`, USB subsystem) and polls CoreAudio device state
  and Logic Pro's performance meter.
- Add a **Classifier agent** that labels detected incidents (buffer
  underrun, device disconnect, sample-rate mismatch, driver restart,
  CPU/thermal overload, unknown).
- Add a **Correlator agent** that cross-references an incident against
  concurrent system events (another app opening, a USB device connecting,
  a sleep/wake cycle, thermal pressure).
- Add a **Report agent** that synthesizes classifier + correlator output
  into a human-readable incident report and appends it to a local log.
- Add a lightweight **incident store** (SQLite) so patterns can be
  reviewed over time (e.g. "80% of your dropouts happen when the audio
  interface + a USB mic are on the same hub").

## Scope

**In scope (v1):**
- macOS only, CoreAudio-based audio interfaces
- Logic Pro as the primary target DAW
- Detection of the 5 incident classes listed above
- Local-only operation (no cloud dependency)
- CLI + local report output (Markdown/JSON); simple daily/weekly summary

**Out of scope (v1, candidate future expansions):**
- Other DAWs (Ableton, Pro Tools)
- Real-time in-session alerting / UI overlay
- Non-macOS platforms
- Generalizing the pipeline to non-audio domains (IoT dropouts, OctoPrint,
  Apple TV streaming) — architecture should allow this later, but it is
  not built in v1

## Impact

- New capability: `audio-triage` (see `specs/audio-triage/spec.md`)
- New local dependency: SQLite (stdlib, no external service)
- No impact to existing systems — this is a new, standalone project
  (initial version of **AudioTriage**)
