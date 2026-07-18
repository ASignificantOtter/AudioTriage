# Tasks: Audio Session Triage Agent

## 1. Project Setup
- [ ] 1.1 Initialize Python project (uv/poetry), repo structure, README skeleton
- [ ] 1.2 Set up SQLite schema for incidents (timestamp, raw_log, class,
      confidence, correlated_cause, report_text)
- [ ] 1.3 Set up config file for API keys, log paths, correlation window,
      confidence threshold

## 2. Collector
- [ ] 2.1 Implement `coreaudiod` log tailer (`log stream` subprocess wrapper)
- [ ] 2.2 Implement USB subsystem log tailer
- [ ] 2.3 Implement CoreAudio device state poller (active devices, sample
      rate, buffer size)
- [ ] 2.4 Implement thermal/CPU sampling fallback (psutil/powermetrics)
- [ ] 2.5 Define "incident candidate" trigger rules (what log patterns
      count as candidates worth classifying)
- [ ] 2.6 Write candidates to SQLite with surrounding context window
- [ ] 2.7 Package as a launchd background agent (runs continuously)

## 3. Classifier Agent
- [ ] 3.1 Write classifier prompt encoding audio-engineering heuristics
      for each incident category
- [ ] 3.2 Implement classifier call (incident candidate -> category +
      confidence)
- [ ] 3.3 Handle low-confidence -> `unknown` fallback
- [ ] 3.4 Unit tests with sample log excerpts for each category

## 4. Correlator Agent
- [ ] 4.1 Implement system event window query (USB, thermal, sleep/wake,
      app activity) around a given incident timestamp
- [ ] 4.2 Write correlator prompt (incident + event window -> likely
      cause + evidence)
- [ ] 4.3 Handle "no correlated event" case explicitly
- [ ] 4.4 Unit tests with synthetic correlated / uncorrelated cases

## 5. Reporter Agent
- [ ] 5.1 Write single-incident report prompt/template
- [ ] 5.2 Implement weekly/periodic summary aggregation query
- [ ] 5.3 Write summary prompt (aggregate incidents -> top patterns)
- [ ] 5.4 Output formats: Markdown file + JSON for programmatic use

## 6. Orchestration
- [ ] 6.1 Implement controller that pulls new candidates and runs them
      through classifier -> correlator -> reporter
- [ ] 6.2 Add CLI entrypoints: `run` (start collector), `report --since`,
      `summary --week`
- [ ] 6.3 Basic error handling / retry for LLM calls

## 7. Validation
- [ ] 7.1 Run against a real Logic Pro session, deliberately trigger at
      least one real incident (e.g. unplug interface mid-session)
- [ ] 7.2 Verify end-to-end: candidate detected -> classified ->
      correlated -> reported correctly
- [ ] 7.3 Collect a week of real usage data for the demo/summary example

## 8. Documentation
- [ ] 8.1 README: what this is, why it exists, architecture diagram
- [ ] 8.2 README: explicit "what I designed vs. what the AI implemented"
      section
- [ ] 8.3 Sample report + sample weekly summary included in repo
- [ ] 8.4 "Future expansions" section noting IoT / OctoPrint / Apple TV
      as candidate generalizations of this architecture
