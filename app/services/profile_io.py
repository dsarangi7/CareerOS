from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import VerificationStatus
from app.models.entities import (
    Achievement,
    CandidateProfile,
    EducationRecord,
    EmploymentRecord,
    EvidenceRecord,
    Project,
    Skill,
)
from app.schemas.evidence import (
    AchievementCreate,
    EducationRecordCreate,
    EmploymentRecordCreate,
    EvidenceRecordCreate,
    ProjectCreate,
    SkillCreate,
)
from app.services.evidence import (
    create_achievement,
    create_education_record,
    create_employment_record,
    create_evidence,
    create_project,
    create_skill,
)

ProfileModel = (
    type[EmploymentRecord] | type[EducationRecord] | type[Skill] | type[Project] | type[Achievement]
)
ProfileCsvTable = tuple[str, ProfileModel]


def export_profile_workbook(session: Session, profile_id: str, output_path: Path) -> Path:
    profile = session.get(CandidateProfile, profile_id)
    if profile is None:
        raise LookupError(profile_id)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        pd.DataFrame(
            [
                {
                    "id": profile.id,
                    "name": profile.name,
                    "current_location": profile.current_location,
                    "origin": profile.origin,
                    "current_role": profile.current_role,
                    "positioning": profile.positioning,
                    "review_notes": profile.review_notes,
                }
            ]
        ).to_excel(writer, sheet_name="Profile", index=False)
        _records_to_frame(session, EmploymentRecord, profile_id).to_excel(
            writer, sheet_name="Employment", index=False
        )
        _records_to_frame(session, EducationRecord, profile_id).to_excel(
            writer, sheet_name="Education", index=False
        )
        _records_to_frame(session, Skill, profile_id).to_excel(
            writer, sheet_name="Skills", index=False
        )
        _records_to_frame(session, Project, profile_id).to_excel(
            writer, sheet_name="Projects", index=False
        )
        _records_to_frame(session, Achievement, profile_id).to_excel(
            writer, sheet_name="Achievements", index=False
        )
        pd.DataFrame(
            [
                {
                    "id": item.id,
                    "achievement_id": item.achievement_id,
                    "title": item.title,
                    "source_type": item.source_type,
                    "source_ref": item.source_ref,
                    "verification_status": _excel_value(item.verification_status),
                }
                for item in session.scalars(
                    select(EvidenceRecord).where(EvidenceRecord.deleted_at.is_(None))
                )
            ]
        ).to_excel(writer, sheet_name="Evidence", index=False)
        pd.DataFrame(
            [
                {
                    "field": "verification_status",
                    "allowed_values": ", ".join(item.value for item in VerificationStatus),
                },
                {
                    "field": "source_ref",
                    "allowed_values": (
                        "Path, URL, note, or source identifier. Do not paste secrets."
                    ),
                },
            ]
        ).to_excel(writer, sheet_name="Data dictionary", index=False)
    return output_path


def import_profile_workbook(session: Session, profile_id: str, input_path: Path) -> dict[str, int]:
    if session.get(CandidateProfile, profile_id) is None:
        raise LookupError(profile_id)
    workbook = pd.read_excel(input_path, sheet_name=None)
    counts = {"skills": 0, "achievements": 0, "evidence": 0}

    for row in workbook.get("Skills", pd.DataFrame()).to_dict(orient="records"):
        name = str(row.get("name", "")).strip()
        if not name:
            continue
        create_skill(
            session,
            profile_id,
            SkillCreate(
                name=name,
                category=str(row.get("category") or "technical"),
                verification_status=_status(row.get("verification_status")),
            ),
        )
        counts["skills"] += 1

    title_to_id: dict[str, str] = {}
    for row in workbook.get("Achievements", pd.DataFrame()).to_dict(orient="records"):
        title = str(row.get("title", "")).strip()
        if not title:
            continue
        achievement = create_achievement(
            session,
            profile_id,
            AchievementCreate(
                title=title,
                description=str(row.get("description") or ""),
                verification_status=_status(row.get("verification_status")),
                evidence_strength=str(row.get("evidence_strength") or "needs_review"),
            ),
        )
        title_to_id[title] = achievement.id
        counts["achievements"] += 1

    for row in workbook.get("Evidence", pd.DataFrame()).to_dict(orient="records"):
        title = str(row.get("title", "")).strip()
        if not title:
            continue
        achievement_id = _nullable_string(row.get("achievement_id"))
        if achievement_id is None:
            achievement_title = _nullable_string(row.get("achievement_title"))
            achievement_id = title_to_id.get(achievement_title or "")
        create_evidence(
            session,
            EvidenceRecordCreate(
                achievement_id=achievement_id,
                title=title,
                source_type=str(row.get("source_type") or "import"),
                source_ref=str(row.get("source_ref") or ""),
                verification_status=_status(row.get("verification_status")),
            ),
        )
        counts["evidence"] += 1
    return counts


def export_profile_csv_bundle(session: Session, profile_id: str, output_dir: Path) -> Path:
    profile = session.get(CandidateProfile, profile_id)
    if profile is None:
        raise LookupError(profile_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "id": profile.id,
                "name": profile.name,
                "current_location": profile.current_location,
                "origin": profile.origin,
                "current_role": profile.current_role,
                "positioning": profile.positioning,
                "review_notes": profile.review_notes,
            }
        ]
    ).to_csv(output_dir / "profile.csv", index=False)
    csv_tables: list[ProfileCsvTable] = [
        ("employment.csv", EmploymentRecord),
        ("education.csv", EducationRecord),
        ("skills.csv", Skill),
        ("projects.csv", Project),
        ("achievements.csv", Achievement),
    ]
    for filename, model in csv_tables:
        _records_to_frame(session, model, profile_id).to_csv(output_dir / filename, index=False)
    pd.DataFrame(
        [
            {
                "id": item.id,
                "achievement_id": item.achievement_id,
                "title": item.title,
                "source_type": item.source_type,
                "source_ref": item.source_ref,
                "verification_status": _excel_value(item.verification_status),
            }
            for item in session.scalars(
                select(EvidenceRecord).where(EvidenceRecord.deleted_at.is_(None))
            )
        ]
    ).to_csv(output_dir / "evidence.csv", index=False)
    return output_dir


def import_profile_csv_bundle(session: Session, profile_id: str, input_dir: Path) -> dict[str, int]:
    if session.get(CandidateProfile, profile_id) is None:
        raise LookupError(profile_id)
    counts = {
        "employment": 0,
        "education": 0,
        "skills": 0,
        "projects": 0,
        "achievements": 0,
        "evidence": 0,
    }

    for row in _read_csv(input_dir / "employment.csv"):
        employer = _required(row, "employer")
        title = _required(row, "title")
        create_employment_record(
            session,
            profile_id,
            EmploymentRecordCreate(
                employer=employer,
                title=title,
                location=_nullable_string(row.get("location")),
                start_date=_nullable_string(row.get("start_date")),
                end_date=_nullable_string(row.get("end_date")),
                verification_status=_status(row.get("verification_status")),
                notes=str(row.get("notes") or ""),
            ),
        )
        counts["employment"] += 1

    for row in _read_csv(input_dir / "education.csv"):
        create_education_record(
            session,
            profile_id,
            EducationRecordCreate(
                institution=_required(row, "institution"),
                degree=_required(row, "degree"),
                field=_nullable_string(row.get("field")),
                start_date=_nullable_string(row.get("start_date")),
                end_date=_nullable_string(row.get("end_date")),
                verification_status=_status(row.get("verification_status")),
            ),
        )
        counts["education"] += 1

    for row in _read_csv(input_dir / "skills.csv"):
        create_skill(
            session,
            profile_id,
            SkillCreate(
                name=_required(row, "name"),
                category=str(row.get("category") or "technical"),
                verification_status=_status(row.get("verification_status")),
            ),
        )
        counts["skills"] += 1

    for row in _read_csv(input_dir / "projects.csv"):
        create_project(
            session,
            profile_id,
            ProjectCreate(
                name=_required(row, "name"),
                summary=str(row.get("summary") or ""),
                verification_status=_status(row.get("verification_status")),
            ),
        )
        counts["projects"] += 1

    title_to_id: dict[str, str] = {}
    for row in _read_csv(input_dir / "achievements.csv"):
        achievement = create_achievement(
            session,
            profile_id,
            AchievementCreate(
                title=_required(row, "title"),
                description=str(row.get("description") or ""),
                verification_status=_status(row.get("verification_status")),
                evidence_strength=str(row.get("evidence_strength") or "needs_review"),
            ),
        )
        title_to_id[achievement.title] = achievement.id
        counts["achievements"] += 1

    for row in _read_csv(input_dir / "evidence.csv"):
        achievement_id = _nullable_string(row.get("achievement_id"))
        if achievement_id is None:
            achievement_id = title_to_id.get(str(row.get("achievement_title") or ""))
        create_evidence(
            session,
            EvidenceRecordCreate(
                achievement_id=achievement_id,
                title=_required(row, "title"),
                source_type=str(row.get("source_type") or "import"),
                source_ref=str(row.get("source_ref") or ""),
                verification_status=_status(row.get("verification_status")),
            ),
        )
        counts["evidence"] += 1
    return counts


def _records_to_frame(session: Session, model: ProfileModel, profile_id: str) -> pd.DataFrame:
    rows = [
        {
            column.name: _excel_value(getattr(record, column.name))
            for column in model.__table__.columns
            if column.name != "deleted_at"
        }
        for record in session.scalars(
            select(model).where(model.profile_id == profile_id, model.deleted_at.is_(None))
        )
    ]
    return pd.DataFrame(rows)


def _status(value: object) -> VerificationStatus:
    text = str(value or VerificationStatus.REQUIRES_CONFIRMATION.value).strip()
    try:
        return VerificationStatus(text)
    except ValueError:
        return VerificationStatus.REQUIRES_CONFIRMATION


def _nullable_string(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _read_csv(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return list(pd.read_csv(path).to_dict(orient="records"))


def _required(row: dict[str, object], key: str) -> str:
    value = _nullable_string(row.get(key))
    if value is None:
        raise ValueError(f"Missing required CSV field: {key}")
    return value


def _excel_value(value: object) -> object:
    if isinstance(value, VerificationStatus):
        return value.value
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    return value
