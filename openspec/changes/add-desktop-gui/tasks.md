# Tasks: Add Desktop GUI

## 1. Service Layer Extraction
- [x] 1.1 Identify CLI-only logic that should move behind reusable application
      services
- [x] 1.2 Add shared services for collector status, incident queries, summary
      queries, safe actions, and configuration validation
- [x] 1.3 Refactor CLI entrypoints to call the shared services instead of
      embedding orchestration flow directly
- [x] 1.4 Add tests covering the shared service behavior where practical

## 2. GUI Foundation
- [x] 2.1 Add the chosen Python-native desktop UI framework and app entrypoint
- [x] 2.2 Create the main application shell and navigation for dashboard,
      incidents, summaries, and settings
- [x] 2.3 Define UI-facing models/view-models so widgets do not depend on raw
      database rows

## 3. Read-First Screens
- [x] 3.1 Implement dashboard view showing collector status, recent incident
      counts, top categories, and top causes
- [x] 3.2 Implement incidents view with sortable/filterable incident history
- [x] 3.3 Implement incident detail view with report text and raw context
- [x] 3.4 Implement summaries view for browsing generated summaries and opening
      exported files
- [x] 3.5 Implement settings view showing current configuration and validation
      results

## 4. Safe Operator Actions
- [x] 4.1 Add UI actions for processing unreported incidents and generating
      weekly/custom summaries
- [x] 4.2 Add UI actions for opening Markdown/JSON report outputs
- [x] 4.3 Add minimal start/stop collector controls consistent with the current
      local execution model

## 5. Quality and Validation
- [x] 5.1 Add or update tests for refactored CLI and new service boundaries
- [x] 5.2 Run existing linting and test workflows after GUI/service changes
- [x] 5.3 Verify the app can launch locally, read the existing SQLite database,
      and surface reports/summaries without requiring terminal use

## 6. Documentation
- [x] 6.1 Update README with GUI purpose, launch instructions, and current
      scope
- [x] 6.2 Document any new dependency, packaging considerations, and known v1
      GUI limitations
