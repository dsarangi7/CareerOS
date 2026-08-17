from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import JobStatus, RecommendationBand, SponsorshipStatus


class JobOpportunityCreate(BaseModel):
    company: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=250)
    location: str | None = None
    country: str | None = None
    source_url: str | None = None
    source_text: str = ""


class JobOpportunityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    location: str | None
    country: str | None
    source_url: str | None
    status: JobStatus
    extraction_confidence: float


class SponsorshipAssessmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    classification: SponsorshipStatus
    evidence_fragment: str
    confidence: float
    human_reviewed: bool


class FitAssessmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    total_score: float
    recommendation: RecommendationBand | str
    category_scores: dict[str, float]
    explanation: dict[str, object]
    confidence: float
