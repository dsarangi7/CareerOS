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
