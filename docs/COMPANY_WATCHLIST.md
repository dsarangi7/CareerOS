# CareerOS Company Watchlist Operational Notes

## Scope

The watchlist monitors official career pages and public job feeds for battery analytics, BMS, SOC/SOH, battery modelling, industrial AI, scientific software, RAG, marine electrification, BESS, and technical solution engineering roles.

The system does not automatically apply for positions and does not use unsupported candidate claims.

## Source Order

1. Official public ATS API
2. Official careers JSON or XML feed
3. Official company careers HTML
4. Licensed job API
5. Email alert
6. Optional compliant external extraction service such as Apify
7. Manual import

LinkedIn or job aggregators must not replace official postings when official postings are available.

## Commands

```powershell
python -m scripts.tasks migrate
python -m scripts.tasks seed-watchlist
python -m scripts.tasks scan-tier-a
python -m scripts.tasks scan-tier-b
python -m scripts.tasks scan-tier-c
python -m scripts.tasks scan-tier-a-live-sample
python -m scripts.tasks scan-approved-live-set
python -m scripts.tasks watchlist-weekly-report
```

## Schedule

- Tier A: daily at 07:00 Asia/Shanghai local time
- Tier B: Monday, Wednesday, Friday at 07:00 Asia/Shanghai local time
- Tier C: Monday at 07:00 Asia/Shanghai local time
- Weekly report: Monday at 07:00 Asia/Shanghai local time

Windows Task Scheduler can recover missed runs with `StartWhenAvailable`. Installation requires human approval:

```powershell
pwsh -ExecutionPolicy Bypass -File scripts/install_job_watch_tasks.ps1
```

Removal affects only CareerOS watchlist tasks:

```powershell
pwsh -ExecutionPolicy Bypass -File scripts/remove_job_watch_tasks.ps1
```

## Validation Policy

Normal unit tests use synthetic fixtures only and make no live external requests. Live career-page validation is opt-in through `scan-tier-a-live-sample` and is intentionally limited to five Tier-A companies for first-run safety.

## Private Data Policy

Do not commit retrieved application data, CVs, personal evidence, recruiter communications, API keys, salary records, local databases, or private reports. Official company metadata in `data/watchlist/battery_company_watchlist.json` is safe to commit.

## Current Limitations

Careers URLs seeded from public company metadata are marked pending until a live scan verifies them. Inaccessible pages, CAPTCHAs, login-only pages, and uncertain ATS detections are routed to manual review.

## Pre-Scheduler Audit Controls

- `scan-tier-a-live-sample` scans the first five Tier-A companies by canonical-name order and is not the approved validation set.
- `scan-approved-live-set` scans only Microvast, QuantumScape, Fluence, TWAICE, and Corvus Energy.
- Generic careers homepages, search-result pages, empty descriptions, missing titles, navigation links, privacy pages, talent-community pages, duplicate requisitions, expired postings, and redirected error pages must not be stored as valid active jobs.
- Every active stored job must have an individual official posting URL or a source-specific external job ID with a verified application URL.
- 403, timeout, TLS, DNS, redirect, and 404 failures route to manual review and do not disable the company permanently.
- The dashboard manual-review queue exposes failed URL, failure type, HTTP status, last attempt, retry count, suggested resolution, manual replacement URL, Retry Scan, and Mark Resolved controls.

Reviewed official source updates from the pre-scheduler audit:

- A123 Systems: `https://www.a123systems.com/join_us/p-12-6.html`
- BYD: `https://job-boards.greenhouse.io/byd`
- QuantumScape: `https://careers.quantumscape.com/go/All/9869900/`
- Fluence: `https://fluenceenergy.wd12.myworkdayjobs.com/fluenceenergy-jobs`
- TWAICE: `https://twaice.jobs.personio.de/?language=en`
- Corvus Energy: `https://corvusenergy.teamtailor.com/`
