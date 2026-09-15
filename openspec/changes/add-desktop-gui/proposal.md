# Proposal: Add Desktop GUI

## Why

AudioTriage already has the core backend needed to collect incidents, classify
them, correlate likely causes, and write local reports. The current experience,
however, is entirely CLI-driven. That makes the project harder to demo, harder
to inspect during day-to-day use, and harder to extend safely because every new
capability would need to assume command-line workflows first.

Before expanding diagnostics scope, AudioTriage should gain a local desktop UI
that makes the existing pipeline usable without requiring terminal commands. The
goal is not a product rewrite. The goal is a thin desktop layer over the
existing single-user, local, macOS-first pipeline.

## What Changes

- Add a Python-native desktop GUI for local use on top of the existing CLI
  pipeline and SQLite-backed data model.
- Introduce reusable application services for incident browsing, summary
  browsing, configuration loading/validation, collector status, and safe
  pipeline actions.
- Surface the existing data and outputs through core screens:
  dashboard, incidents, incident detail, summaries, and settings.
- Add a small set of v1 controls for starting/stopping collection, generating
  reports, generating summaries, opening exported files, and validating
  configuration.
- Preserve the CLI as a supported interface by moving backend logic behind
  reusable service boundaries instead of duplicating behavior in the GUI.

## Scope

**In scope (v1):**
- A local desktop app built with a Python-native UI framework
- Read-first views for dashboard, incidents, incident details, and summaries
- Collector health/status visibility
- Settings display and validation for existing config values
- Safe operator controls that trigger existing workflows
- Reuse of the current SQLite store and generated Markdown/JSON outputs

**Out of scope (v1):**
- Rewriting the collector, classifier, correlator, or reporter logic
- Introducing a web stack or multi-user architecture
- Real-time overlays, notifications, or in-session DAW integrations
- Generalizing beyond the current macOS-first local workflow
- Expanding incident taxonomy or diagnostics features as part of the UI change

## Impact

- New capability: desktop GUI for AudioTriage
- New architectural boundary: shared application services used by both CLI and
  GUI
- Likely new dependency: Python desktop UI toolkit unless the chosen framework
  can be satisfied from the standard library
- No intended change to the existing incident-processing model or local-only
  storage approach
