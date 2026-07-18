# Capability: Audio Triage

## Overview

The system SHALL detect, classify, and explain audio incidents (dropouts,
glitches, device disconnects) occurring during Logic Pro sessions on
macOS, producing human-readable root-cause reports without requiring the
user to manually inspect system logs.

## Requirements

### Requirement: Incident Detection

The system SHALL continuously monitor macOS unified logs and CoreAudio
device state to detect audio incidents while Logic Pro is running.

#### Scenario: Buffer underrun detected

- **WHEN** `coreaudiod` logs a buffer underrun or overload event
- **THEN** the system SHALL record an incident candidate with the exact
  timestamp and surrounding log context (±30 seconds)

#### Scenario: Audio device disconnects mid-session

- **WHEN** an active CoreAudio output/input device is removed while
  Logic Pro is the active application
- **THEN** the system SHALL record an incident candidate tagged with the
  device name and last-known sample rate/buffer size

### Requirement: Incident Classification

The system SHALL classify each recorded incident into one of a defined
set of categories, using an LLM-based classifier informed by audio
engineering heuristics.

#### Scenario: Classifier labels a known pattern

- **WHEN** an incident candidate is passed to the classifier agent
- **THEN** the system SHALL return one of: `buffer_underrun`,
  `device_disconnect`, `sample_rate_mismatch`, `driver_restart`,
  `cpu_thermal_overload`, or `unknown`, along with a confidence score

#### Scenario: Classifier cannot confidently label an incident

- **WHEN** the classifier's confidence falls below a defined threshold
- **THEN** the incident SHALL be labeled `unknown` and flagged for
  inclusion in the raw log excerpt of the report, rather than forcing an
  incorrect category

### Requirement: Root-Cause Correlation

The system SHALL attempt to identify a likely cause for each classified
incident by correlating it against concurrent system events.

#### Scenario: Dropout correlates with USB event

- **WHEN** a classified incident's timestamp falls within a configurable
  window (default 10s) of a USB device connect/disconnect/power event
- **THEN** the correlator agent SHALL include that USB event as a
  candidate cause with supporting evidence in its output

#### Scenario: No correlated event found

- **WHEN** no system event is found within the correlation window
- **THEN** the correlator agent SHALL report "no correlated system event
  found" rather than fabricating a cause

### Requirement: Human-Readable Reporting

The system SHALL generate a plain-English report for each incident and
SHALL support rolling up incidents into a periodic summary.

#### Scenario: Single incident report

- **WHEN** an incident has been classified and correlated
- **THEN** the system SHALL produce a report entry stating what happened,
  when, the likely cause, and the supporting evidence, in a format
  readable by a non-technical user

#### Scenario: Weekly summary

- **WHEN** the user requests a summary for a given date range
- **THEN** the system SHALL aggregate incidents by category and
  correlated cause, surfacing the most frequent pattern(s)

### Requirement: Local-Only Operation

The system SHALL operate entirely on the local machine without requiring
external network services for its core detection and storage functions.

#### Scenario: No network dependency for core function

- **WHEN** the collector, classifier, correlator, and reporter run
- **THEN** all log access, state polling, and incident storage SHALL
  occur locally, with the only external dependency being the LLM API
  calls used by the classifier/correlator/reporter agents
