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
