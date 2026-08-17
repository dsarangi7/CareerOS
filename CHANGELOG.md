# Changelog

## 0.1.0 - 2026-08-17

- Created CareerOS monorepo structure.
- Added Phase 1 foundation: configuration, database, core entities, seed system, health API, dashboard shell, tests, and validation scripts.
- Added deterministic sponsorship classification, scoring, approval-gated status transitions, and demo XLSX export.
- Verified API and dashboard startup locally.
- Added first Phase 2 profile/evidence CRUD API slice for skills, achievements, and evidence records.
- Expanded Phase 2 with employment, education, project CRUD endpoints, review queue summaries, verification updates, soft deletion, profile workbook export/import service, and dashboard edit controls.
- Added safe field updates for profile/evidence records and CSV bundle export/import helpers.
- Started Phase 3 with deterministic job ingestion, requirement extraction, duplicate detection, sponsorship assessment, fit scoring, and assessment API endpoints.
- Added CSV, XLSX, and JSON job import service and CLI command using the deterministic ingestion pipeline.
- Completed a practical Phase 3 CRM workflow bridge with application creation, ready-to-apply, and approval-gated applied status.
- Completed first Phase 4 tailored CV generation slice with claim validation, PDF rendering, validation results, and human approval request records.
- Completed first Phase 5 agent integration slice with typed contracts, mock adapter, optional OpenAI adapter, guardrails, tracing records, and agent API endpoints.
