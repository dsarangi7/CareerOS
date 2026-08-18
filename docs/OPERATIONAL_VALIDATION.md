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

## Company Watchlist Pre-Scheduler Audit - 2026-08-18

### Reconciliation

The earlier controlled live scan used `scan-tier-a-live-sample`, which selected the first five Tier-A companies by canonical-name order. That was not the approved five-company validation set.

Earlier scanned companies:

- A123 Systems
- ABB Marine & Ports
- ACCURE Battery Intelligence
- BYD
- CATL

Reason A123 Systems and BYD appeared:

- They were in the first five Tier-A records after sorting by `priority_tier` and `canonical_name`.
- The approved validation set was not intentionally changed.
- Historical scan records were preserved.

The earlier two captured records were generic careers/about-page text from ABB Marine & Ports and ACCURE Battery Intelligence, not valid individual job postings. They were not deleted; both records were marked `rejected_generic_source`.

### Corrections

- Added explicit `scan-approved-live-set` command for Microvast, QuantumScape, Fluence, TWAICE, and Corvus Energy.
- Added source failure records for HTTP/access failures instead of summary-only failure tracking.
- Added raw, normalized, rejected, and duplicate counters.
- Added stricter validation for individual job postings.
- Added manual-review queue controls in the dashboard.
- Updated public watchlist metadata for reviewed official source URLs.

### Approved Five-Company Scan

Command:

```powershell
python -m scripts.tasks scan-approved-live-set
```

Result:

- Microvast: `https://microvast.com/careers/`, TLS certificate verification failure in local Python runtime, manual review required.
- QuantumScape: `https://careers.quantumscape.com/go/All/9869900/`, HTTP 200, SuccessFactors, 26 raw candidates, 2 normalized jobs, 22 rejected candidates.
- Fluence: `https://fluenceenergy.wd12.myworkdayjobs.com/fluenceenergy-jobs`, HTTP 200, Workday, 0 raw candidates through current HTML connector.
- TWAICE: `https://twaice.jobs.personio.de/?language=en`, HTTP 200, static HTML/Personio source, 5 raw candidates, 0 normalized jobs, 5 rejected candidates.
- Corvus Energy: `https://corvusenergy.teamtailor.com/`, HTTP 200, Teamtailor, 11 raw candidates, 0 normalized jobs, 11 rejected candidates.

Approved-set totals:

- Successful page checks: 4.
- Manual-review failures: 1.
- Raw job records: 42.
- Normalized jobs: 2.
- Duplicates removed: 0.
- Rejected records: 38.
- New jobs captured: 2.
- Changed jobs: 0.
- Expired jobs: 0.

### A123 and BYD Follow-Up

- A123 Systems alternate official source: `https://www.a123systems.com/join_us/p-12-6.html`, HTTP 200, 27 raw candidates, 0 normalized jobs, 27 rejected candidates.
- BYD alternate official source: `https://job-boards.greenhouse.io/byd`, HTTP 200, Greenhouse, 9 raw candidates, 4 normalized jobs, 5 rejected candidates.

The original BYD timeout was a response-time/access failure against `https://www.bydglobal.com/en/careers`. It is now resolved by routing BYD North America checks to the official Greenhouse board while preserving the historical timeout source record.

### Validation

Command:

```powershell
python -m scripts.tasks validate
```

Result:

- Ruff format check: passed.
- Ruff lint: passed.
- Mypy strict check: passed.
- Pytest: 44 passed, 1 skipped.
- Security scan: passed.
- API smoke check: passed.
- Dashboard smoke check: passed.
- Docker check: skipped because Docker executable was not available.

Opt-in live integration test:

```powershell
$env:CAREEROS_RUN_LIVE_WATCHLIST_TESTS='1'
python -m pytest tests/integration/test_watchlist_live_opt_in.py -q
```

Result: passed.

### Scheduler Readiness

Recommendation: not ready to install recurring Windows scheduled tasks yet.

Reasons:

- Microvast still requires manual review due local TLS certificate verification failure.
- Official ATS-specific extraction should be improved for Workday, Personio, and Teamtailor before broad unattended scans.
- Approved-set scan is now bounded and auditable, but source coverage is not yet mature enough for unattended daily operation.

No Windows scheduled tasks were installed.
