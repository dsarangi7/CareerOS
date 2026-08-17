# Validation

Run:

```powershell
python -m scripts.tasks validate
```

This checks formatting, linting, typing, tests, and demo XLSX export generation.

Additional Phase 2 export:

```powershell
python -m scripts.tasks export-profile
```

This writes the current profile/evidence workbook to `data/exports/career_os_profile_export.xlsx`.

CSV bundle export:

```powershell
python -m scripts.tasks export-profile-csv
```

This writes editable CSV files to `data/exports/career_os_profile_csv/`.

Phase 3 job ingestion is covered by integration tests in:

```powershell
python -m pytest tests/integration/test_job_ingestion_phase3.py
python -m pytest tests/integration/test_job_file_import_phase3.py
```

Import jobs from a file:

```powershell
python -m scripts.tasks import-jobs --path data/fixtures/jobs.csv
```

Supported file types for this command are CSV, XLSX, and JSON.

Phase 4 CV generation is covered by:

```powershell
python -m pytest tests/integration/test_phase4_cv_generation.py
```

The CV test renders a PDF with ReportLab and validates that pypdf can extract readable text.

Phase 5 agent contracts and guardrails are covered by:

```powershell
python -m pytest tests/unit/test_phase5_agents.py
python -m pytest tests/integration/test_phase5_agent_api.py
```
