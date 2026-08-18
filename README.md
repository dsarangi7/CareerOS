# CareerOS

CareerOS is a local-first personal career-management platform for maintaining a verified career record, assessing job opportunities, managing applications, and preparing truthful application materials.

## Quick Start

```powershell
cd C:\Users\admin\Downloads\career-os
python -m scripts.tasks setup
python -m scripts.tasks migrate
python -m scripts.tasks seed
python -m scripts.tasks validate
python -m scripts.tasks export-profile
python -m scripts.tasks export-profile-csv
python -m scripts.tasks security-scan
python -m scripts.tasks api-smoke
python -m scripts.tasks dashboard-smoke
```

Run the API:

```powershell
python -m uvicorn app.api.main:app --reload
```

Ingest a pasted job description through `POST /opportunities/ingest`.

Import jobs from a local CSV, XLSX, or JSON file:

```powershell
python -m scripts.tasks import-jobs --path path\to\jobs.csv
```

Generate a tailored CV draft through `POST /opportunities/{job_id}/tailored-cv`; generated CVs stay local and require human approval before publishing or sharing.

Inspect and run local mock agents:

```powershell
python -m pytest tests/unit/test_phase5_agents.py
```

The default agent provider is `mock`; OpenAI integration is optional and configured through environment variables.

Track communications, follow-ups, interviews, prep packs, outcomes, and weekly summaries through the API:

```text
POST /applications/{application_id}/communications
POST /applications/{application_id}/follow-ups
GET /follow-ups/overdue
POST /applications/{application_id}/interviews
POST /interviews/{interview_id}/preparation-pack
POST /applications/{application_id}/outcomes
POST /reports/weekly
```

Create a local SQLite backup:

```powershell
python -m scripts.tasks backup-db
```

Run the dashboard:

```powershell
python -m streamlit run dashboard/Home.py
```

## Windows Launcher

Create and install the virtual environment first:

```powershell
cd G:\AI_WORKSPACE\CareerOS
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install .
```

Start both local services safely:

```powershell
.\start-careeros.ps1
```

The launcher verifies `.venv`, checks dependencies, runs migrations, starts FastAPI on `127.0.0.1:8000`, starts Streamlit on `127.0.0.1:8501`, waits for both services, and opens `http://localhost:8501`.

Stop only the processes started by the launcher:

```powershell
.\stop-careeros.ps1
```

If PowerShell blocks local scripts, run this once for the current shell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Current Scope

Phases 1-7 are implemented as local-first vertical slices: profile/evidence management, job ingestion and scoring, application workflow, tailored CV generation, guarded agents, CRM reporting, workbook export, and security/privacy hardening checks.

See `docs/FINAL_COMPLETION_REPORT.md` for the final acceptance summary, limitations, and first-use workflows.

## Company Watchlist and Job Discovery

CareerOS includes a battery-company watchlist for official career-page monitoring. The watchlist stores public company metadata, scan status, ATS/source observations, active/relevant job counts, sponsorship signals, and manual-review flags.

Common commands:

```powershell
python -m scripts.tasks seed-watchlist
python -m scripts.tasks scan-tier-a
python -m scripts.tasks scan-tier-b
python -m scripts.tasks scan-tier-c
python -m scripts.tasks watchlist-weekly-report
```

A bounded live validation scan is available for the first five Tier-A companies only:

```powershell
python -m scripts.tasks scan-tier-a-live-sample
```

The Streamlit dashboard has a `Company Watchlist` page with filters for tier, country, company, segment, and scan status, plus company detail and relevant-job tables.

Windows Task Scheduler scripts are available but should only be installed after human approval:

```powershell
pwsh -ExecutionPolicy Bypass -File scripts/install_job_watch_tasks.ps1
pwsh -ExecutionPolicy Bypass -File scripts/remove_job_watch_tasks.ps1
```

The scheduler scripts create or remove only `CareerOS-JobWatch-*` tasks. They do not stop unrelated Python processes and do not apply to jobs automatically.

Apify is optional. Configure actor IDs only if approved and needed after official sources are exhausted:

```powershell
$env:APIFY_API_TOKEN=""
$env:APIFY_LINKEDIN_ACTOR_ID=""
$env:APIFY_INDEED_ACTOR_ID=""
$env:APIFY_EURES_ACTOR_ID=""
```
