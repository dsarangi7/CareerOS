# Operational Validation

## Phase

CareerOS Real-Data Onboarding and Operational Validation.

## Rules

- Do not add new major features during this phase.
- Do not commit real personal data, CVs, employer-confidential documents, recruiter communications, salary records, application data, API keys, or private local databases.
- Use local-only ignored paths for real-data onboarding.
- Stop before real CV tailoring until the master profile is human approved.

## Repository Verification

- Repository path: `G:\AI_WORKSPACE\CareerOS`
- Remote: `https://github.com/dsarangi7/CareerOS.git`
- Pull command: `git pull --ff-only origin main`
- Pull result: already up to date.
- HEAD requirement: `a92df0b` or descendant.
- Actual HEAD at phase start: `a92df0b`.
- Result: passed.

## Documents Read

- `docs/FINAL_COMPLETION_REPORT.md`
- `docs/SECURITY_REVIEW.md`
- `docs/USER_GUIDE.md`
- `docs/PROGRESS.md`
- `docs/DATA_MODEL.md`

## Validation Run

Command:

```powershell
python -m scripts.tasks validate
```

Result:

- `ruff format --check`: passed.
- `ruff check`: passed.
- `mypy app scripts tests`: passed with 55 source files checked.
- `pytest`: 27 passed.
- `security-scan`: passed with no obvious secret patterns found.
- `api-smoke`: passed.
- `dashboard-smoke`: passed.
- `docker-check`: Docker executable not installed; Docker startup skipped.
- Export generation: completed by validation suite.

Warnings:

- FastAPI/TestClient emitted the known upstream StarletteDeprecationWarning about `httpx`.

## Documented Versus Actual Results

- Validation results matched the documented final results.
- Environment exception matched documentation: Docker is not installed locally, so live Docker startup is skipped.
- Documentation drift found: `docs/FINAL_COMPLETION_REPORT.md` still shows the old setup path `C:\Users\admin\Downloads\career-os`; actual repository path is `G:\AI_WORKSPACE\CareerOS`.

## Local-Only Workspace

Required ignored paths:

- `private_input/cv/`
- `private_input/evidence/`
- `private_input/jobs/`
- `private_input/communications/`
- `private_output/tailored_cvs/`
- `private_output/reports/`
- `private_data/`

Status:

- `.gitignore` updated to exclude `private_input/`, `private_output/`, and `private_data/`.
- `.gitignore` also updated to exclude the pre-existing `input/` folder because it contains real local CV/source files.
- Local-only directories created.
- Git ignore verification passed for all required local-only paths.
- Local-only onboarding checklist template created at `private_data/onboarding_checklist_template.csv`.

## Onboarding Checklist Categories

Every career fact must be classified as one of:

- Verified
- User confirmed
- Evidence pending
- In progress
- Planned
- Unsupported
- Confidential and CV-ineligible

Uncertain dates, exact titles, metrics, ownership, institutional wording, publications, awards, visa facts, compensation details, and relocation preferences require explicit human review.

## Report Plan

After a local CV or structured career source is confirmed, generate these local-only reports under `private_output/reports/`:

1. Master Career Profile
2. Employment Timeline
3. Education Timeline
4. Achievement Bank
5. Project Bank
6. Skill Inventory
7. Evidence Coverage Report
8. Missing Information Report
9. Contradiction Report
10. CV Eligibility Report

## Job Validation Plan

After master profile approval, import five real historical job descriptions covering:

1. Battery Diagnostics
2. Battery Modelling
3. BMS Data Analysis
4. Industrial AI or Data Science
5. RAG or Engineering Software

For each job, record requirement extraction, sponsorship classification, fit score, hard restrictions, evidence mapping, confidence, unverifiable assumptions, and manual-score comparison.

## Local CV Source Availability

- Local CV-like source files are available under ignored local input folders.
- Multiple candidate source files were found, so no import was performed automatically.
- Required next human confirmation: select the exact CV/source file that should be treated as the initial import source.

## Current Blocker

Awaiting explicit confirmation of the local CV/source file to import and human confirmation of uncertain career facts. No real-data import has been performed yet.
