import json
from pathlib import Path
from typing import Any, TypedDict

import pandas as pd
from sqlalchemy.orm import Session

from app.models.entities import (
    JobFitAssessment,
    JobOpportunity,
    JobRequirement,
    SponsorshipAssessment,
)
from app.services.jobs import ingest_job_description


class ImportedJob(TypedDict):
    job_id: str
    duplicate_of: str | None
    requirement_count: int
    sponsorship_id: str
    fit_assessment_id: str


class JobImportSummary(TypedDict):
    imported: int
    duplicates: int
    jobs: list[ImportedJob]


def import_jobs_from_file(session: Session, input_path: Path) -> JobImportSummary:
    rows = _load_rows(input_path)
    imported_jobs: list[ImportedJob] = []
    duplicate_count = 0
    for row in rows:
        source_text = _source_text_from_row(row)
        job, duplicate_of, requirements, sponsorship, fit = ingest_job_description(
            session,
            source_text=source_text,
            source_url=_nullable_string(row.get("source_url")),
            default_company=_string_or_default(row.get("company"), "Unknown Company"),
            default_title=_string_or_default(row.get("title"), "Untitled Role"),
        )
        if duplicate_of is not None:
            duplicate_count += 1
        imported_jobs.append(
            _imported_job(
                job=job,
                duplicate_of=duplicate_of,
                requirements=requirements,
                sponsorship=sponsorship,
                fit=fit,
            )
        )
    return {"imported": len(imported_jobs), "duplicates": duplicate_count, "jobs": imported_jobs}


def _load_rows(input_path: Path) -> list[dict[str, object]]:
    suffix = input_path.suffix.lower()
    if suffix == ".csv":
        return list(pd.read_csv(input_path).to_dict(orient="records"))
    if suffix in {".xlsx", ".xls"}:
        return list(pd.read_excel(input_path).to_dict(orient="records"))
    if suffix == ".json":
        raw = json.loads(input_path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            raw = raw.get("jobs", [raw])
        if not isinstance(raw, list):
            raise ValueError(
                "JSON job import must be an object, a list, or an object with a jobs list"
            )
        return [_coerce_mapping(item) for item in raw]
    raise ValueError(f"Unsupported job import file type: {suffix}")


def _coerce_mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("Each imported JSON job must be an object")
    return {str(key): item for key, item in value.items()}


def _source_text_from_row(row: dict[str, object]) -> str:
    direct_text = _nullable_string(
        row.get("source_text") or row.get("description") or row.get("job_description")
    )
    if direct_text:
        return direct_text
    lines = [
        f"Company: {_string_or_default(row.get('company'), 'Unknown Company')}",
        f"Title: {_string_or_default(row.get('title'), 'Untitled Role')}",
    ]
    for source_key, label in [
        ("location", "Location"),
        ("country", "Country"),
        ("requirements", "Required"),
        ("skills", "Required skill"),
        ("visa", "Visa"),
        ("source_url", "Source URL"),
    ]:
        value = _nullable_string(row.get(source_key))
        if value:
            lines.append(f"{label}: {value}")
    return "\n".join(lines)


def _imported_job(
    *,
    job: JobOpportunity,
    duplicate_of: str | None,
    requirements: list[JobRequirement],
    sponsorship: SponsorshipAssessment,
    fit: JobFitAssessment,
) -> ImportedJob:
    return {
        "job_id": job.id,
        "duplicate_of": duplicate_of,
        "requirement_count": len(requirements),
        "sponsorship_id": sponsorship.id,
        "fit_assessment_id": fit.id,
    }


def _nullable_string(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _string_or_default(value: object, default: str) -> str:
    return _nullable_string(value) or default
