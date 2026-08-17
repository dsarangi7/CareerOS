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
from app.schemas.evidence import AchievementCreate, EvidenceRecordCreate, SkillCreate
from app.services.evidence import create_achievement, create_evidence, create_skill

ProfileModel = (
    type[EmploymentRecord] | type[EducationRecord] | type[Skill] | type[Project] | type[Achievement]
)


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


def _excel_value(value: object) -> object:
    if isinstance(value, VerificationStatus):
        return value.value
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    return value
