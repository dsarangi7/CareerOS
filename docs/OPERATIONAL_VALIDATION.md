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

## Battery Company Watchlist and Scheduled Job Discovery - 2026-08-18

### Commands Run

```powershell
python -m scripts.tasks migrate
python -m scripts.tasks seed-watchlist
python -m scripts.tasks scan-tier-a
python -m scripts.tasks validate
python -m scripts.tasks scan-tier-a-live-sample
python -m scripts.tasks validate
```

### Implementation Results

- Added 77 public company watchlist records across Tier A, Tier B, and Tier C.
- Added persistent watchlist tables for companies, jobs, job assessments, job sources, and scan runs.
- Added offline-safe scan commands for Tier A/B/C and weekly report generation.
- Added bounded opt-in live scan command for the first five Tier-A companies.
- Added optional Apify environment placeholders without actor IDs or tokens.
- Added Company Watchlist Streamlit page with filters, company detail view, scan status, relevant jobs, sponsorship observations, and manual-review flags.
- Added Windows Task Scheduler scripts that affect only `CareerOS-JobWatch-*` tasks.

### Validation Results

Final validation passed:

- Ruff format check: passed.
- Ruff lint: passed.
- Mypy strict check: passed.
- Pytest: 42 passed, 1 skipped.
- Skipped test: live careers-page integration test, intentionally opt-in only.
- Security scan: passed, no obvious secret patterns found.
- API smoke check: passed.
- Dashboard smoke check: passed.
- Docker check: skipped because Docker executable was not available on this machine.

### Controlled Live Scan

Command:

```powershell
python -m scripts.tasks scan-tier-a-live-sample
```

Result:

- Companies attempted: first five Tier-A companies in canonical-name order.
- Successful page checks: 3.
- New jobs captured: 2.
- Changed jobs: 0.
- Expired jobs: 0.
- Manual-review failures: 2.

Failures routed to manual review:

- A123 Systems: official careers page returned HTTP 403.
- BYD: official careers page timed out during the controlled sample.

### Defects Found and Fixed

- Live HTML fallback initially reused generic careers-page URLs as application URLs, causing false duplicate merging and noisy changed-job counts.
- Fixed by separating `original_url` from `application_url` and deduping generic careers-page discoveries by company/title/location.
- Added regression coverage to prevent generic careers pages from becoming canonical application URLs.
- Added an intra-scan duplicate guard so repeated title fragments on the same page do not churn scan history.

### Decisions

- Official company sources remain preferred over LinkedIn or aggregators.
- Inaccessible pages, CAPTCHAs, login-only pages, and uncertain ATS results are manual-review items.
- Apify is optional only and must not run when official sources provide equivalent job data.
- Windows scheduled tasks were not installed; installation requires explicit human approval.

### Unresolved Questions

- Confirm whether to install Windows Task Scheduler tasks for `CareerOS-JobWatch-*`.
- Confirm whether live verification should continue company-by-company for the remaining watchlist records.
- Confirm which countries and sponsorship patterns should receive highest priority once the approved master profile is finalized.
