# Progress

## 2026-08-17

### Phase 0

- Workspace inspected: `C:\Users\admin\Downloads` was not a git repository.
- No `AGENTS.md` existed in the workspace root.
- Created project under `C:\Users\admin\Downloads\career-os` to avoid touching unrelated downloaded files.
- Environment: Python 3.11.9 available; Python 3.12 not available in PATH. Dependencies installed into user Python.
- GNU `make` was not available, but Makefile targets are mirrored through `python -m scripts.tasks`.

### Phase 1

- Implemented project configuration, database layer, entities, seed data, FastAPI app, dashboard shell, deterministic scoring, sponsorship classification, export, and tests.
- Validation command: `python -m scripts.tasks validate`.
- Validation result: passed on 2026-08-17.
  - `ruff format --check`: passed.
  - `ruff check`: passed.
  - `mypy app scripts tests`: passed with 27 source files checked.
  - `pytest`: 8 passed, 1 upstream FastAPI/TestClient deprecation warning.
  - Demo XLSX export generated at `data/exports/career_os_demo_export.xlsx`.
- API startup check: `python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8010` started successfully and was stopped.
- Dashboard startup check: `python -m streamlit run dashboard/Home.py --server.headless true --server.port 8510 --browser.gatherUsageStats false` started successfully and was stopped.

### Deferred to Phase 2+

- Full CRUD APIs and editable dashboard forms for profile/evidence records.
- Alembic revision file generation beyond metadata-backed local migration.
- Polished XLSX formatting, dropdown validation, formulas, and frozen panes.
- Full CV rendering and claim validation workflow.

### Phase 2

- Implemented first profile/evidence CRUD slice:
  - `GET/POST /profiles/{profile_id}/skills`
  - `GET/POST /profiles/{profile_id}/achievements`
  - `GET/POST /evidence`
- Added typed Pydantic schemas and deterministic service functions for skills, achievements, and evidence records.
- Added API integration test using an isolated SQLite in-memory database.
- Validation result after Phase 2 slice: passed on 2026-08-17.
  - `ruff format --check`: passed.
  - `ruff check`: passed.
  - `mypy app scripts tests`: passed with 30 source files checked.
  - `pytest`: 9 passed, 1 upstream FastAPI/TestClient deprecation warning.
- Continued Phase 2 profile/evidence implementation:
  - Added `GET/POST /profiles/{profile_id}/employment`.
  - Added `GET/POST /profiles/{profile_id}/education`.
  - Added `GET/POST /profiles/{profile_id}/projects`.
  - Added `GET /profiles/{profile_id}/review-queue`.
  - Added `PATCH /records/{record_type}/{record_id}/verification`.
  - Added `DELETE /records/{record_type}/{record_id}` with soft deletion.
  - Added profile workbook export/import service and `python -m scripts.tasks export-profile`.
  - Added editable Streamlit controls for profile, achievements, evidence, and review verification.
- Validation result after expanded Phase 2 slice: passed on 2026-08-17.
  - `ruff format --check`: passed.
  - `ruff check`: passed.
  - `mypy app scripts tests`: passed with 32 source files checked.
  - `pytest`: 10 passed, 1 upstream FastAPI/TestClient deprecation warning.
  - Demo CRM XLSX export and profile workbook export generated successfully.
