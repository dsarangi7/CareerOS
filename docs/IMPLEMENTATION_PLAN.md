# Implementation Plan

## Phase 0

- Inspect repository and protect unrelated user files.
- Create implementation, progress, and decision trackers.
- Establish validation commands and environment assumptions.

## Phase 1 Foundation

- Create Python project configuration, Makefile targets, Docker skeleton, and environment template.
- Build SQLAlchemy database layer with UUID IDs, timestamps, soft deletion fields, indexes, and enums.
- Implement core entities requested by the product brief.
- Add seed system for Dibya Jyoti Sarangi with uncertain facts marked for review.
- Add FastAPI health/profile/opportunities endpoints.
- Add Streamlit dashboard shell with overview, opportunities, profile, and review queue.
- Add deterministic scoring and sponsorship primitives needed by the seed demo.
- Add tests and validation command.

## Next Phases

- Phase 2: full profile/evidence CRUD and import/export.
- Phase 3: richer job ingestion, extraction, deduplication, scoring views, and status CRM.
- Phase 4: CV templates, claim validation reports, PDF rendering, and approval gates.
- Phase 5: typed agent interfaces, mock adapters, optional OpenAI adapter, guardrails.
- Phase 6: communications, interviews, reporting, XLSX formatting.
- Phase 7: hardening, accessibility, backup/restore, full security review.
