from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import get_session
from app.models.entities import Achievement, CandidateProfile, EvidenceRecord, JobOpportunity, Skill
from app.schemas.evidence import (
    AchievementCreate,
    AchievementRead,
    EvidenceRecordCreate,
    EvidenceRecordRead,
    SkillCreate,
    SkillRead,
)
from app.schemas.jobs import JobOpportunityCreate, JobOpportunityRead
from app.schemas.profile import CandidateProfileRead
from app.services.evidence import (
    AchievementNotFoundError,
    ProfileNotFoundError,
    create_achievement,
    create_evidence,
    create_skill,
    list_achievements,
    list_evidence,
    list_skills,
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
