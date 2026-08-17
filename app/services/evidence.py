from datetime import UTC, datetime
from typing import cast

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
from app.services.audit import record_audit


class ProfileNotFoundError(LookupError):
    pass


class AchievementNotFoundError(LookupError):
    pass


class RecordNotFoundError(LookupError):
    pass


RecordModel = (
    type[EmploymentRecord]
    | type[EducationRecord]
    | type[Skill]
    | type[Project]
    | type[Achievement]
    | type[EvidenceRecord]
)
RecordEntity = EmploymentRecord | EducationRecord | Skill | Project | Achievement | EvidenceRecord


def get_profile_or_raise(session: Session, profile_id: str) -> CandidateProfile:
    profile = session.get(CandidateProfile, profile_id)
    if profile is None:
        raise ProfileNotFoundError(profile_id)
    return profile


def list_employment_records(session: Session, profile_id: str) -> list[EmploymentRecord]:
    get_profile_or_raise(session, profile_id)
    query = (
        select(EmploymentRecord)
        .where(EmploymentRecord.profile_id == profile_id, EmploymentRecord.deleted_at.is_(None))
        .order_by(EmploymentRecord.created_at.desc())
    )
    return list(session.scalars(query))


def create_employment_record(
    session: Session, profile_id: str, payload: EmploymentRecordCreate
) -> EmploymentRecord:
    get_profile_or_raise(session, profile_id)
    record = EmploymentRecord(profile_id=profile_id, **payload.model_dump())
    session.add(record)
    session.flush()
    record_audit(
        session,
        action="create_employment_record",
        subject_type="EmploymentRecord",
        subject_id=record.id,
    )
    return record


def list_education_records(session: Session, profile_id: str) -> list[EducationRecord]:
    get_profile_or_raise(session, profile_id)
    query = (
        select(EducationRecord)
        .where(EducationRecord.profile_id == profile_id, EducationRecord.deleted_at.is_(None))
        .order_by(EducationRecord.created_at.desc())
    )
    return list(session.scalars(query))


def create_education_record(
    session: Session, profile_id: str, payload: EducationRecordCreate
) -> EducationRecord:
    get_profile_or_raise(session, profile_id)
    record = EducationRecord(profile_id=profile_id, **payload.model_dump())
    session.add(record)
    session.flush()
    record_audit(
        session,
        action="create_education_record",
        subject_type="EducationRecord",
        subject_id=record.id,
    )
    return record


def list_skills(session: Session, profile_id: str) -> list[Skill]:
    get_profile_or_raise(session, profile_id)
    return list(
        session.scalars(
            select(Skill)
            .where(Skill.profile_id == profile_id, Skill.deleted_at.is_(None))
            .order_by(Skill.name)
        )
    )


def create_skill(session: Session, profile_id: str, payload: SkillCreate) -> Skill:
    get_profile_or_raise(session, profile_id)
    skill = Skill(profile_id=profile_id, **payload.model_dump())
    session.add(skill)
    session.flush()
    record_audit(session, action="create_skill", subject_type="Skill", subject_id=skill.id)
    return skill


def list_projects(session: Session, profile_id: str) -> list[Project]:
    get_profile_or_raise(session, profile_id)
    return list(
        session.scalars(
            select(Project)
            .where(Project.profile_id == profile_id, Project.deleted_at.is_(None))
            .order_by(Project.name)
        )
    )


def create_project(session: Session, profile_id: str, payload: ProjectCreate) -> Project:
    get_profile_or_raise(session, profile_id)
    project = Project(profile_id=profile_id, **payload.model_dump())
    session.add(project)
    session.flush()
    record_audit(session, action="create_project", subject_type="Project", subject_id=project.id)
    return project


def list_achievements(session: Session, profile_id: str) -> list[Achievement]:
    get_profile_or_raise(session, profile_id)
    return list(
        session.scalars(
            select(Achievement)
            .where(Achievement.profile_id == profile_id, Achievement.deleted_at.is_(None))
            .order_by(Achievement.title)
        )
    )


def create_achievement(
    session: Session, profile_id: str, payload: AchievementCreate
) -> Achievement:
    get_profile_or_raise(session, profile_id)
    achievement = Achievement(profile_id=profile_id, **payload.model_dump())
    session.add(achievement)
    session.flush()
    record_audit(
        session,
        action="create_achievement",
        subject_type="Achievement",
        subject_id=achievement.id,
        details={"verification_status": achievement.verification_status.value},
    )
    return achievement


def list_evidence(session: Session, achievement_id: str | None = None) -> list[EvidenceRecord]:
    query = (
        select(EvidenceRecord)
        .where(EvidenceRecord.deleted_at.is_(None))
        .order_by(EvidenceRecord.created_at.desc())
    )
    if achievement_id is not None:
        query = query.where(EvidenceRecord.achievement_id == achievement_id)
    return list(session.scalars(query))


def create_evidence(session: Session, payload: EvidenceRecordCreate) -> EvidenceRecord:
    if (
        payload.achievement_id is not None
        and session.get(Achievement, payload.achievement_id) is None
    ):
        raise AchievementNotFoundError(payload.achievement_id)
    evidence = EvidenceRecord(**payload.model_dump())
    session.add(evidence)
    session.flush()
    record_audit(
        session,
        action="create_evidence",
        subject_type="EvidenceRecord",
        subject_id=evidence.id,
        details={"verification_status": evidence.verification_status.value},
    )
    return evidence


def update_verification_status(
    session: Session,
    model: RecordModel,
    record_id: str,
    status: VerificationStatus,
) -> RecordEntity:
    record = cast(RecordEntity | None, session.get(model, record_id))
    if record is None or record.deleted_at is not None:
        raise RecordNotFoundError(record_id)
    record.verification_status = status
    record_audit(
        session,
        action="update_verification_status",
        subject_type=model.__name__,
        subject_id=record.id,
        details={"verification_status": status.value},
    )
    return record


def soft_delete_record(session: Session, model: RecordModel, record_id: str) -> RecordEntity:
    record = cast(RecordEntity | None, session.get(model, record_id))
    if record is None or record.deleted_at is not None:
        raise RecordNotFoundError(record_id)
    record.deleted_at = datetime.now(UTC)
    record_audit(
        session, action="soft_delete_record", subject_type=model.__name__, subject_id=record.id
    )
    return record


ReviewQueueItem = dict[str, str | None]


def get_review_queue(session: Session, profile_id: str) -> dict[str, list[ReviewQueueItem]]:
    get_profile_or_raise(session, profile_id)
    pending_statuses = [
        VerificationStatus.USER_REPORTED_PENDING_EVIDENCE,
        VerificationStatus.IN_PROGRESS,
        VerificationStatus.PLANNED,
        VerificationStatus.INFERRED,
        VerificationStatus.UNSUPPORTED,
        VerificationStatus.REQUIRES_CONFIRMATION,
    ]
    return {
        "employment": [
            _queue_item(item, item.title, item.employer)
            for item in session.scalars(
                select(EmploymentRecord).where(
                    EmploymentRecord.profile_id == profile_id,
                    EmploymentRecord.deleted_at.is_(None),
                    EmploymentRecord.verification_status.in_(pending_statuses),
                )
            )
        ],
        "education": [
            _queue_item(item, item.degree, item.institution)
            for item in session.scalars(
                select(EducationRecord).where(
                    EducationRecord.profile_id == profile_id,
                    EducationRecord.deleted_at.is_(None),
                    EducationRecord.verification_status.in_(pending_statuses),
                )
            )
        ],
        "skills": [
            _queue_item(item, item.name, item.category)
            for item in session.scalars(
                select(Skill).where(
                    Skill.profile_id == profile_id,
                    Skill.deleted_at.is_(None),
                    Skill.verification_status.in_(pending_statuses),
                )
            )
        ],
        "projects": [
            _queue_item(item, item.name, None)
            for item in session.scalars(
                select(Project).where(
                    Project.profile_id == profile_id,
                    Project.deleted_at.is_(None),
                    Project.verification_status.in_(pending_statuses),
                )
            )
        ],
        "achievements": [
            _queue_item(item, item.title, item.evidence_strength)
            for item in session.scalars(
                select(Achievement).where(
                    Achievement.profile_id == profile_id,
                    Achievement.deleted_at.is_(None),
                    Achievement.verification_status.in_(pending_statuses),
                )
            )
        ],
    }


def _queue_item(record: RecordEntity, label: str, context: str | None) -> ReviewQueueItem:
    return {
        "id": record.id,
        "label": label,
        "context": context,
        "verification_status": _status_value(record.verification_status),
    }


def _status_value(status: VerificationStatus | str) -> str:
    return status.value if isinstance(status, VerificationStatus) else status
