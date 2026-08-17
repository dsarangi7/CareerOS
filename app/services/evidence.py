from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Achievement, CandidateProfile, EvidenceRecord, Skill
from app.schemas.evidence import AchievementCreate, EvidenceRecordCreate, SkillCreate
from app.services.audit import record_audit


class ProfileNotFoundError(LookupError):
    pass


class AchievementNotFoundError(LookupError):
    pass


def get_profile_or_raise(session: Session, profile_id: str) -> CandidateProfile:
    profile = session.get(CandidateProfile, profile_id)
    if profile is None:
        raise ProfileNotFoundError(profile_id)
    return profile


def list_skills(session: Session, profile_id: str) -> list[Skill]:
    get_profile_or_raise(session, profile_id)
    return list(
        session.scalars(select(Skill).where(Skill.profile_id == profile_id).order_by(Skill.name))
    )


def create_skill(session: Session, profile_id: str, payload: SkillCreate) -> Skill:
    get_profile_or_raise(session, profile_id)
    skill = Skill(profile_id=profile_id, **payload.model_dump())
    session.add(skill)
    session.flush()
    record_audit(session, action="create_skill", subject_type="Skill", subject_id=skill.id)
    return skill


def list_achievements(session: Session, profile_id: str) -> list[Achievement]:
    get_profile_or_raise(session, profile_id)
    return list(
        session.scalars(
            select(Achievement)
            .where(Achievement.profile_id == profile_id)
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
    query = select(EvidenceRecord).order_by(EvidenceRecord.created_at.desc())
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
