from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import VerificationStatus


class SkillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str = Field(default="technical", max_length=120)
    verification_status: VerificationStatus = VerificationStatus.USER_REPORTED_PENDING_EVIDENCE


class SkillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profile_id: str
    name: str
    category: str
    verification_status: VerificationStatus


class AchievementCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    verification_status: VerificationStatus = VerificationStatus.USER_REPORTED_PENDING_EVIDENCE
    evidence_strength: str = "needs_review"


class AchievementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profile_id: str
    title: str
    description: str
    verification_status: VerificationStatus
    evidence_strength: str


class EvidenceRecordCreate(BaseModel):
    achievement_id: str | None = None
    title: str = Field(min_length=1, max_length=200)
    source_type: str = Field(min_length=1, max_length=80)
    source_ref: str = ""
    verification_status: VerificationStatus = VerificationStatus.REQUIRES_CONFIRMATION


class EvidenceRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    achievement_id: str | None
    title: str
    source_type: str
    source_ref: str
    verification_status: VerificationStatus
