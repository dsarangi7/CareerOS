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

Run the dashboard:

```powershell
python -m streamlit run dashboard/Home.py
```

## Current Scope

Phase 1 foundation is implemented: configuration, database models, seed data, health API, dashboard shell, deterministic workflow primitives, tests, and validation commands.
