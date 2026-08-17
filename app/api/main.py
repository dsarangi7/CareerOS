from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.enums import VerificationStatus
from app.db.base import get_session
from app.models.entities import (
    Achievement,
    CandidateProfile,
    EducationRecord,
    EmploymentRecord,
    EvidenceRecord,
    JobOpportunity,
    Project,
    Skill,
)
from app.schemas.evidence import (
    AchievementCreate,
    AchievementRead,
    EducationRecordCreate,
    EducationRecordRead,
    EmploymentRecordCreate,
    EmploymentRecordRead,
    EvidenceRecordCreate,
    EvidenceRecordRead,
    ProjectCreate,
    ProjectRead,
    SkillCreate,
    SkillRead,
    VerificationUpdate,
)
from app.schemas.jobs import JobOpportunityCreate, JobOpportunityRead
from app.schemas.profile import CandidateProfileRead
from app.services.evidence import (
    AchievementNotFoundError,
    ProfileNotFoundError,
    RecordModel,
    RecordNotFoundError,
    ReviewQueueItem,
    create_achievement,
    create_education_record,
    create_employment_record,
    create_evidence,
    create_project,
    create_skill,
    get_review_queue,
    list_achievements,
    list_education_records,
    list_employment_records,
    list_evidence,
    list_projects,
    list_skills,
    soft_delete_record,
    update_verification_status,
)
from app.services.jobs import create_job

app = FastAPI(title="CareerOS", version="0.1.0")
SessionDep = Annotated[Session, Depends(get_session)]


@app.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {"status": "ok", "env": settings.env}


@app.get("/profile", response_model=CandidateProfileRead)
def get_profile(session: SessionDep) -> CandidateProfile:
    profile = session.scalar(select(CandidateProfile).order_by(CandidateProfile.created_at))
    if profile is None:
        raise HTTPException(status_code=404, detail="Seed profile not found. Run the seed command.")
    return profile


@app.get("/opportunities", response_model=list[JobOpportunityRead])
def list_opportunities(session: SessionDep) -> list[JobOpportunity]:
    return list(session.scalars(select(JobOpportunity).order_by(JobOpportunity.created_at.desc())))


@app.post("/opportunities", response_model=JobOpportunityRead, status_code=201)
def post_opportunity(payload: JobOpportunityCreate, session: SessionDep) -> JobOpportunity:
    job = create_job(
        session,
        company_name=payload.company,
        title=payload.title,
        location=payload.location,
        country=payload.country,
        source_url=payload.source_url,
        source_text=payload.source_text,
    )
    session.commit()
    return job


@app.get("/profiles/{profile_id}/employment", response_model=list[EmploymentRecordRead])
def get_employment_records(profile_id: str, session: SessionDep) -> list[EmploymentRecord]:
    try:
        return list_employment_records(session, profile_id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Profile not found") from exc


@app.post("/profiles/{profile_id}/employment", response_model=EmploymentRecordRead, status_code=201)
def post_employment_record(
    profile_id: str, payload: EmploymentRecordCreate, session: SessionDep
) -> EmploymentRecord:
    try:
        record = create_employment_record(session, profile_id, payload)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Profile not found") from exc
    session.commit()
    return record


@app.get("/profiles/{profile_id}/education", response_model=list[EducationRecordRead])
def get_education_records(profile_id: str, session: SessionDep) -> list[EducationRecord]:
    try:
        return list_education_records(session, profile_id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Profile not found") from exc


@app.post("/profiles/{profile_id}/education", response_model=EducationRecordRead, status_code=201)
def post_education_record(
    profile_id: str, payload: EducationRecordCreate, session: SessionDep
) -> EducationRecord:
    try:
        record = create_education_record(session, profile_id, payload)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Profile not found") from exc
    session.commit()
    return record


@app.get("/profiles/{profile_id}/skills", response_model=list[SkillRead])
def get_skills(profile_id: str, session: SessionDep) -> list[Skill]:
    try:
        return list_skills(session, profile_id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Profile not found") from exc


@app.post("/profiles/{profile_id}/skills", response_model=SkillRead, status_code=201)
def post_skill(profile_id: str, payload: SkillCreate, session: SessionDep) -> Skill:
    try:
        skill = create_skill(session, profile_id, payload)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Profile not found") from exc
    session.commit()
    return skill


@app.get("/profiles/{profile_id}/projects", response_model=list[ProjectRead])
def get_projects(profile_id: str, session: SessionDep) -> list[Project]:
    try:
        return list_projects(session, profile_id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Profile not found") from exc


@app.post("/profiles/{profile_id}/projects", response_model=ProjectRead, status_code=201)
def post_project(profile_id: str, payload: ProjectCreate, session: SessionDep) -> Project:
    try:
        project = create_project(session, profile_id, payload)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Profile not found") from exc
    session.commit()
    return project


@app.get("/profiles/{profile_id}/achievements", response_model=list[AchievementRead])
def get_achievements(profile_id: str, session: SessionDep) -> list[Achievement]:
    try:
        return list_achievements(session, profile_id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Profile not found") from exc


@app.post("/profiles/{profile_id}/achievements", response_model=AchievementRead, status_code=201)
def post_achievement(
    profile_id: str, payload: AchievementCreate, session: SessionDep
) -> Achievement:
    try:
        achievement = create_achievement(session, profile_id, payload)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Profile not found") from exc
    session.commit()
    return achievement


@app.get("/evidence", response_model=list[EvidenceRecordRead])
def get_evidence(session: SessionDep, achievement_id: str | None = None) -> list[EvidenceRecord]:
    return list_evidence(session, achievement_id)


@app.post("/evidence", response_model=EvidenceRecordRead, status_code=201)
def post_evidence(payload: EvidenceRecordCreate, session: SessionDep) -> EvidenceRecord:
    try:
        evidence = create_evidence(session, payload)
    except AchievementNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Achievement not found") from exc
    session.commit()
    return evidence


@app.get("/profiles/{profile_id}/review-queue")
def review_queue(profile_id: str, session: SessionDep) -> dict[str, list[ReviewQueueItem]]:
    try:
        return get_review_queue(session, profile_id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Profile not found") from exc


RECORD_MODELS: dict[str, RecordModel] = {
    "employment": EmploymentRecord,
    "education": EducationRecord,
    "skills": Skill,
    "projects": Project,
    "achievements": Achievement,
    "evidence": EvidenceRecord,
}


@app.patch("/records/{record_type}/{record_id}/verification")
def patch_verification(
    record_type: str, record_id: str, payload: VerificationUpdate, session: SessionDep
) -> dict[str, str]:
    model = RECORD_MODELS.get(record_type)
    if model is None:
        raise HTTPException(status_code=404, detail="Record type not found")
    try:
        record = update_verification_status(
            session,
            model,
            record_id,
            VerificationStatus(payload.verification_status),
        )
    except RecordNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Record not found") from exc
    session.commit()
    return {"id": record.id, "verification_status": payload.verification_status.value}


@app.delete("/records/{record_type}/{record_id}", status_code=204)
def delete_record(record_type: str, record_id: str, session: SessionDep) -> None:
    model = RECORD_MODELS.get(record_type)
    if model is None:
        raise HTTPException(status_code=404, detail="Record type not found")
    try:
        soft_delete_record(session, model, record_id)
    except RecordNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Record not found") from exc
    session.commit()
