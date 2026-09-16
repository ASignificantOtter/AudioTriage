# Design: Add Desktop GUI

## Context

AudioTriage already has a complete backend-oriented v1 shape:

- collector for incident candidates
- orchestrator for classification/correlation/reporting
- SQLite as the system of record
- Markdown and JSON report outputs
- CLI entrypoints for running collection, processing reports, and building
  summaries

The GUI should sit on top of those capabilities instead of replacing them. This
change prioritizes usability and visibility over feature expansion.

## Architecture

The GUI will be introduced as a thin desktop client over a shared application
service layer.

```text
┌──────────────────────────────────────────────────────────┐
│                    Desktop GUI                           │
│ dashboard | incidents | summaries | settings            │
└───────────────┬──────────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────────────┐
│              Application Services                        │
│ status | incident queries | summary queries | actions    │
└───────┬──────────────────────────────┬───────────────────┘
        │                              │
┌───────▼─────────┐          ┌─────────▼──────────────────┐
│ Existing CLI    │          │ Existing backend pipeline  │
│ entrypoints     │          │ collector/orchestrator     │
└─────────────────┘          └──────────┬─────────────────┘
                                        │
                              ┌─────────▼──────────┐
                              │ SQLite + reports   │
                              └────────────────────┘
```

## UI Framework Direction

For v1, the GUI should use a Python-native desktop framework that keeps the
project single-language and local-first. The preferred direction is a framework
that minimizes moving parts and keeps packaging straightforward for a macOS
desktop app.

This design assumes a single in-process desktop app rather than a local web
server or split frontend/backend deployment.

## Service Boundaries

The GUI should not talk directly to orchestration internals or scatter SQL
through widget code. Instead, shared services should expose stable operations:

- **Collector status service**
  - determine whether collection is running
  - surface last-seen activity and basic health signals
- **Incident service**
  - list incidents with sorting/filtering support
  - load a single incident with full details
- **Summary service**
  - list available summaries
  - build weekly/custom summaries from existing pipeline logic
- **Action service**
  - start collector
  - stop collector
  - process unreported incidents
  - open generated report files
- **Settings service**
  - load current configuration
  - validate required paths and thresholds

These services should be reusable from the CLI so the GUI does not become a
second implementation of business behavior.

## Screen Model

### Dashboard

The dashboard should provide an at-a-glance operational view:

- collector status
- incident count in recent periods
- top incident categories
- top correlated causes
- latest generated report or summary

### Incidents View

The incidents screen should present SQLite-backed history in a browsable table:

- timestamp
- classification
- confidence
- correlated cause
- report presence

It should support basic filtering and selection without requiring the user to
open generated files manually.

### Incident Detail View

Selecting an incident should reveal:

- full timestamp
- class and confidence
- correlated cause and evidence
- raw incident context
- rendered report text

### Summaries View

The summaries screen should let the user:

- browse generated summaries
- trigger a weekly summary
- generate a custom range summary
- open Markdown/JSON outputs

### Settings View

The settings screen should initially focus on visibility and validation:

- config path
- database path
- output path
- log binary/system tool paths
- thresholds

Editing may be added, but validation and clarity matter more than full settings
management in v1.

## Key Decisions

1. **Read-first UX before control-heavy UX.**
   The first value is visibility into collected data and generated outputs.
   Operational controls stay intentionally small.

2. **Shared services before widgets.**
   Reusable service boundaries must be created before significant UI work so the
   CLI and GUI share behavior.

3. **Reuse SQLite and report files as existing sources of truth.**
   No new persistence model should be introduced for the GUI.

4. **Local desktop app, not web app.**
   A desktop UI matches the current single-user, local-only, macOS-first scope
   and avoids introducing an unnecessary frontend stack.

5. **Keep the backend pipeline intact.**
   The GUI is a usability layer over current functionality, not a rewrite of
   collector/orchestrator responsibilities.

## Risks and Mitigations

- **Risk: GUI code couples directly to backend internals**
  - Mitigation: require a service layer and UI-specific models

- **Risk: collector process control is platform-sensitive**
  - Mitigation: start with health/status visibility and only a minimal set of
    safe controls aligned with existing launch behavior

- **Risk: framework choice adds packaging complexity**
  - Mitigation: prefer a Python-native framework with low operational overhead
    and validate packaging early

- **Risk: UI work distracts from core diagnostics**
  - Mitigation: scope v1 to presenting and triggering existing capabilities,
    not expanding analysis logic
