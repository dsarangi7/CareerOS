import json
from pathlib import Path

import pandas as pd

from app.models.entities import JobOpportunity
from app.services.job_import import import_jobs_from_file


def test_import_jobs_from_csv_xlsx_and_json(session, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    csv_path = tmp_path / "jobs.csv"
    xlsx_path = tmp_path / "jobs.xlsx"
    json_path = tmp_path / "jobs.json"
    rows = [
        {
            "company": "Import Battery Co",
            "title": "BMS Data Analysis Engineer",
            "location": "Berlin",
            "country": "Germany",
            "source_url": "https://example.test/import/bms",
            "requirements": "Required Python, BMS, SOC, SOH and battery diagnostics experience.",
            "visa": "Visa sponsorship may sponsor exceptional candidates.",
        },
        {
            "company": "Import Battery Co",
            "title": "BMS Data Analysis Engineer",
            "location": "Berlin",
            "country": "Germany",
            "source_url": "https://example.test/import/bms-copy",
            "requirements": "Required Python and BMS experience.",
        },
    ]
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    pd.DataFrame(rows[:1]).to_excel(xlsx_path, index=False)
    json_path.write_text(json.dumps({"jobs": rows[:1]}), encoding="utf-8")

    csv_summary = import_jobs_from_file(session, csv_path)
    xlsx_summary = import_jobs_from_file(session, xlsx_path)
    json_summary = import_jobs_from_file(session, json_path)
    session.commit()

    assert csv_summary["imported"] == 2
    assert csv_summary["duplicates"] == 1
    assert xlsx_summary["imported"] == 1
    assert json_summary["imported"] == 1
    assert session.query(JobOpportunity).count() == 4
