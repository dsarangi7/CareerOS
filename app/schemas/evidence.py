from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import VerificationStatus


class SkillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str = Field(default="technical", max_length=120)
    verification_status: VerificationStatus = VerificationStatus.USER_REPORTED_PENDING_EVIDENCE


class VerificationUpdate(BaseModel):
    verification_status: VerificationStatus


class EmploymentRecordCreate(BaseModel):
    employer: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    start_date: str | None = Field(default=None, max_length=20)
    end_date: str | None = Field(default=None, max_length=20)
    verification_status: VerificationStatus = VerificationStatus.REQUIRES_CONFIRMATION
    notes: str = ""


class EmploymentRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profile_id: str
    employer: str
    title: str
    location: str | None
    start_date: str | None
    end_date: str | None
    verification_status: VerificationStatus
    notes: str


class EducationRecordCreate(BaseModel):
    institution: str = Field(min_length=1, max_length=200)
    degree: str = Field(min_length=1, max_length=200)
    field: str | None = Field(default=None, max_length=200)
    start_date: str | None = Field(default=None, max_length=20)
    end_date: str | None = Field(default=None, max_length=20)
    verification_status: VerificationStatus = VerificationStatus.REQUIRES_CONFIRMATION


class EducationRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profile_id: str
    institution: str
    degree: str
    field: str | None
    start_date: str | None
    end_date: str | None
    verification_status: VerificationStatus


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    summary: str = ""
    verification_status: VerificationStatus = VerificationStatus.USER_REPORTED_PENDING_EVIDENCE


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profile_id: str
    name: str
    summary: str
    verification_status: VerificationStatus


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
