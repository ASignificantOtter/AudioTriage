# Design: AudioTriage

## Context

**AudioTriage** is a personal project targeting a single macOS machine
running Logic Pro with one or more external audio interfaces (e.g.
USB/Thunderbolt). Goal is a believable, demo-able diagnostic tool built
with genuine audio-domain judgment behind the classification logic — not
just a generic log correlator.

## Data Sources

| Source | What it gives us | How we get it |
|---|---|---|
| `coreaudiod` unified log | Driver restarts, device add/remove, sample rate changes | `log stream --predicate 'process == "coreaudiod"'` |
| CoreAudio device state | Current sample rate, buffer size, active device list | `AudioObjectGetPropertyData` via `pyobjc` or polling `system_profiler SPAudioDataType` |
| USB subsystem log | Device connect/disconnect, power events, hub topology | `log stream --predicate 'subsystem == "com.apple.iokit.usb"'` |
| Logic Pro performance meter | CPU load, disk I/O, plugin load at time of incident | Best-effort: screen-scrape via Accessibility API, OR user-reported timestamp + system-level CPU sampling as v1 fallback |
| System sleep/thermal state | Thermal pressure, App Nap, sleep/wake | `pmset -g log`, `log stream --predicate 'subsystem == "com.apple.iokit.thermal"'` |

**v1 simplification:** Logic Pro's internal performance meter isn't
exposed via a clean API. For v1, use system-wide CPU/thermal sampling
(`psutil` or `powermetrics`) as a proxy, and note this as a known
limitation. A future iteration could explore Logic's OSC/scripting
support or MIDI-based performance data if available.

## Agent Architecture

```
 ┌─────────────┐     ┌────────────────┐     ┌───────────────┐     ┌──────────────┐
 │  Collector   │ --> │  Classifier    │ --> │  Correlator   │ --> │   Reporter   │
 │ (continuous  │     │  agent         │     │  agent        │     │   agent      │
 │  log/metric  │     │ (label the     │     │ (find likely  │     │ (write human │
 │  polling)    │     │  incident)     │     │  cause)       │     │  report)     │
 └─────────────┘     └────────────────┘     └───────────────┘     └──────────────┘
        │                                                                  │
        └──────────────────── incident store (SQLite) ─────────────────────┘
```

- **Collector**: not an LLM agent — a deterministic Python process that
  tails logs and polls state, writes raw incident candidates (timestamp +
  raw log context) to the store. Runs continuously as a background
  process (launchd agent).
- **Classifier agent**: LLM call given the raw log window around an
  incident; outputs one of the defined incident classes + confidence.
  Prompted with domain context (what buffer underruns look like in
  coreaudiod logs, what a sample-rate mismatch log entry looks like, etc.)
- **Correlator agent**: LLM call given the classified incident + a wider
  window of system events (USB, thermal, sleep/wake, other app activity);
  outputs a most-likely-cause hypothesis with supporting evidence.
- **Reporter agent**: LLM call that turns classifier + correlator output
  into a plain-English report entry, and can roll up multiple incidents
  into a weekly summary ("3 of your 5 dropouts this week happened within
  10s of the external SSD spinning up").

## Key Decisions

1. **Collector is deterministic, not an LLM agent.** Log tailing and
   polling should be cheap and reliable; save LLM calls for the
   judgment-heavy classification/correlation steps. This is a deliberate
   cost and reliability decision worth calling out in the README.
2. **SQLite over a cloud DB.** This is a local, single-user tool — no
   reason to add network dependency or hosting cost.
3. **Agents are separate prompts/functions, not separate processes.**
   For v1, "multi-agent" means a clear separation of responsibility and
   prompt/context per stage, orchestrated by a simple Python controller —
   not a distributed system. This keeps AudioTriage buildable in the
   target timeframe while still demonstrating multi-agent design
   thinking (context isolation, single-responsibility prompts, staged
   handoff).
4. **Domain-informed classification prompts.** The classifier's prompt
   will encode real audio-engineering heuristics (e.g. buffer underruns
   often cluster with high plugin CPU load; sample-rate mismatches often
   follow a device switch) — this is where professional audio diagnosis
   experience should visibly shape the system, not just generic log
   parsing.

## Open Questions

- Best way to get Logic Pro-specific performance data without relying on
  UI scraping — worth a short research spike before committing to the
  v1 fallback.
- Whether to notify in near-real-time (e.g. macOS notification) or purely
  batch/summary — leaning batch for v1 to keep scope tight.
