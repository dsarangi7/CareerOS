# Backup And Restore

Create a local SQLite backup:

```powershell
python -m scripts.tasks backup-db
```

Backups are written to `data/backups/` with a UTC timestamp in the filename.

To restore locally, stop the API/dashboard, copy the chosen backup over `career_os.db`, then run:

```powershell
python -m scripts.tasks validate
```
