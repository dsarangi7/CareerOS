from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ApprovalStatus, JobStatus, SponsorshipStatus, VerificationStatus
from app.db.base import Base


def uuid_str() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class TimestampMixin:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CandidateProfile(TimestampMixin, Base):
    __tablename__ = "candidate_profiles"

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    current_location: Mapped[str | None] = mapped_column(String(200))
    origin: Mapped[str | None] = mapped_column(String(200))
    current_role: Mapped[str | None] = mapped_column(String(200))
    positioning: Mapped[str] = mapped_column(Text, default="")
    review_notes: Mapped[str] = mapped_column(Text, default="")

    employment_records: Mapped[list[EmploymentRecord]] = relationship(back_populates="profile")
    education_records: Mapped[list[EducationRecord]] = relationship(back_populates="profile")
    skills: Mapped[list[Skill]] = relationship(back_populates="profile")
    projects: Mapped[list[Project]] = relationship(back_populates="profile")
    achievements: Mapped[list[Achievement]] = relationship(back_populates="profile")


class EmploymentRecord(TimestampMixin, Base):
    __tablename__ = "employment_records"

    profile_id: Mapped[str] = mapped_column(ForeignKey("candidate_profiles.id"), index=True)
    employer: Mapped[str] = mapped_column(String(200), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[str | None] = mapped_column(String(200))
    start_date: Mapped[str | None] = mapped_column(String(20))
    end_date: Mapped[str | None] = mapped_column(String(20))
    verification_status: Mapped[VerificationStatus] = mapped_column(
        String(50), default=VerificationStatus.REQUIRES_CONFIRMATION
    )
    notes: Mapped[str] = mapped_column(Text, default="")

    profile: Mapped[CandidateProfile] = relationship(back_populates="employment_records")


class EducationRecord(TimestampMixin, Base):
    __tablename__ = "education_records"

    profile_id: Mapped[str] = mapped_column(ForeignKey("candidate_profiles.id"), index=True)
    institution: Mapped[str] = mapped_column(String(200), nullable=False)
    degree: Mapped[str] = mapped_column(String(200), nullable=False)
    field: Mapped[str | None] = mapped_column(String(200))
    start_date: Mapped[str | None] = mapped_column(String(20))
    end_date: Mapped[str | None] = mapped_column(String(20))
    verification_status: Mapped[VerificationStatus] = mapped_column(
        String(50), default=VerificationStatus.REQUIRES_CONFIRMATION
    )

    profile: Mapped[CandidateProfile] = relationship(back_populates="education_records")


class Certification(TimestampMixin, Base):
    __tablename__ = "certifications"

    profile_id: Mapped[str] = mapped_column(ForeignKey("candidate_profiles.id"), index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    issuer: Mapped[str | None] = mapped_column(String(200))
    issued_date: Mapped[str | None] = mapped_column(String(20))
    verification_status: Mapped[VerificationStatus] = mapped_column(
        String(50), default=VerificationStatus.REQUIRES_CONFIRMATION
    )


class Skill(TimestampMixin, Base):
    __tablename__ = "skills"
    __table_args__ = (UniqueConstraint("profile_id", "name", name="uq_profile_skill"),)

    profile_id: Mapped[str] = mapped_column(ForeignKey("candidate_profiles.id"), index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(120), default="technical")
    verification_status: Mapped[VerificationStatus] = mapped_column(String(50))

    profile: Mapped[CandidateProfile] = relationship(back_populates="skills")


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    profile_id: Mapped[str] = mapped_column(ForeignKey("candidate_profiles.id"), index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    verification_status: Mapped[VerificationStatus] = mapped_column(String(50))

    profile: Mapped[CandidateProfile] = relationship(back_populates="projects")


class Achievement(TimestampMixin, Base):
    __tablename__ = "achievements"

    profile_id: Mapped[str] = mapped_column(ForeignKey("candidate_profiles.id"), index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    verification_status: Mapped[VerificationStatus] = mapped_column(String(50))
    evidence_strength: Mapped[str] = mapped_column(String(50), default="needs_review")

    profile: Mapped[CandidateProfile] = relationship(back_populates="achievements")


class EvidenceRecord(TimestampMixin, Base):
    __tablename__ = "evidence_records"

    achievement_id: Mapped[str | None] = mapped_column(ForeignKey("achievements.id"), index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_ref: Mapped[str] = mapped_column(Text, default="")
    verification_status: Mapped[VerificationStatus] = mapped_column(String(50))


class RoleFamily(TimestampMixin, Base):
    __tablename__ = "role_families"

    name: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    scoring_weights: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class CountryPreference(TimestampMixin, Base):
    __tablename__ = "country_preferences"

    country: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    priority: Mapped[int] = mapped_column(default=3)
    notes: Mapped[str] = mapped_column(Text, default="")


class WorkAuthorization(TimestampMixin, Base):
    __tablename__ = "work_authorizations"

    country: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(120), nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="")


class CompensationPreference(TimestampMixin, Base):
    __tablename__ = "compensation_preferences"

    country: Mapped[str] = mapped_column(String(120), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    minimum_total: Mapped[float | None] = mapped_column(Float)
    target_total: Mapped[float | None] = mapped_column(Float)


class Company(TimestampMixin, Base):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    website: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str] = mapped_column(Text, default="")


class WatchCompany(TimestampMixin, Base):
    __tablename__ = "watch_companies"

    canonical_name: Mapped[str] = mapped_column(
        String(200), unique=True, nullable=False, index=True
    )
    alternative_names: Mapped[list[str]] = mapped_column(JSON, default=list)
    parent_company: Mapped[str | None] = mapped_column(String(200))
    company_website: Mapped[str | None] = mapped_column(String(500))
    official_careers_url: Mapped[str | None] = mapped_column(String(1000))
    careers_platform: Mapped[str] = mapped_column(String(120), default="Unknown")
    ats_type: Mapped[str] = mapped_column(String(120), default="Unknown")
    countries_of_operation: Mapped[list[str]] = mapped_column(JSON, default=list)
    major_rnd_locations: Mapped[list[str]] = mapped_column(JSON, default=list)
    battery_segment: Mapped[list[str]] = mapped_column(JSON, default=list)
    company_classification: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_monitoring_frequency: Mapped[str] = mapped_column(String(80), default="weekly")
    priority_tier: Mapped[str] = mapped_column(String(10), index=True)
    geographic_relevance: Mapped[str] = mapped_column(String(120), default="global")
    known_language_requirements: Mapped[str] = mapped_column(Text, default="")
    sponsorship_evidence: Mapped[str] = mapped_column(Text, default="")
    last_careers_page_verification: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_successful_scan: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scan_status: Mapped[str] = mapped_column(String(80), default="pending", index=True)
    active_job_count: Mapped[int] = mapped_column(Integer, default=0)
    relevant_job_count: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str] = mapped_column(Text, default="")
    manual_review_status: Mapped[str] = mapped_column(String(80), default="not_reviewed")

    watch_jobs: Mapped[list[WatchJob]] = relationship(back_populates="company")


class WatchJob(TimestampMixin, Base):
    __tablename__ = "watch_jobs"
    __table_args__ = (
        UniqueConstraint("dedupe_key", name="uq_watch_job_dedupe_key"),
        Index("ix_watch_job_company_title_location", "company_id", "title", "location"),
    )

    company_id: Mapped[str] = mapped_column(ForeignKey("watch_companies.id"), index=True)
    title: Mapped[str] = mapped_column(String(250), nullable=False, index=True)
    original_url: Mapped[str] = mapped_column(String(1000), default="")
    application_url: Mapped[str] = mapped_column(String(1000), default="")
    source: Mapped[str] = mapped_column(String(120), default="official_careers_html")
    external_job_id: Mapped[str | None] = mapped_column(String(250), index=True)
    location: Mapped[str | None] = mapped_column(String(250))
    country: Mapped[str | None] = mapped_column(String(120), index=True)
    work_mode: Mapped[str | None] = mapped_column(String(80))
    publication_date: Mapped[str | None] = mapped_column(String(80))
    retrieval_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    full_description: Mapped[str] = mapped_column(Text, default="")
    department: Mapped[str | None] = mapped_column(String(200))
    seniority: Mapped[str | None] = mapped_column(String(100))
    salary: Mapped[str | None] = mapped_column(String(250))
    required_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    experience_requirement: Mapped[str | None] = mapped_column(Text)
    education_requirement: Mapped[str | None] = mapped_column(Text)
    language_requirement: Mapped[str | None] = mapped_column(Text)
    visa_wording: Mapped[str | None] = mapped_column(Text)
    citizenship_restriction: Mapped[str | None] = mapped_column(Text)
    security_clearance_restriction: Mapped[str | None] = mapped_column(Text)
    closing_date: Mapped[str | None] = mapped_column(String(80))
    content_hash: Mapped[str] = mapped_column(String(64), index=True, default="")
    active_status: Mapped[str] = mapped_column(String(40), default="active", index=True)
    scan_history: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    dedupe_key: Mapped[str] = mapped_column(String(300), nullable=False, index=True)

    company: Mapped[WatchCompany] = relationship(back_populates="watch_jobs")
    assessment: Mapped[WatchJobAssessment | None] = relationship(back_populates="job")


class WatchJobAssessment(TimestampMixin, Base):
    __tablename__ = "watch_job_assessments"

    watch_job_id: Mapped[str] = mapped_column(ForeignKey("watch_jobs.id"), unique=True, index=True)
    fit_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    eligibility_score: Mapped[float] = mapped_column(Float, default=0.0)
    sponsorship_status: Mapped[str] = mapped_column(String(80), default="not_mentioned")
    technical_match: Mapped[list[str]] = mapped_column(JSON, default=list)
    transferable_match: Mapped[list[str]] = mapped_column(JSON, default=list)
    missing_requirements: Mapped[list[str]] = mapped_column(JSON, default=list)
    hard_restrictions: Mapped[list[str]] = mapped_column(JSON, default=list)
    recommended_cv_lane: Mapped[str] = mapped_column(String(120), default="general_engineering")
    recommended_action: Mapped[str] = mapped_column(
        String(120), default="archive_without_notification"
    )
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    evidence_mapping: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    application_urgency: Mapped[str] = mapped_column(String(80), default="low")

    job: Mapped[WatchJob] = relationship(back_populates="assessment")


class WatchJobSource(TimestampMixin, Base):
    __tablename__ = "watch_job_sources"

    company_id: Mapped[str] = mapped_column(ForeignKey("watch_companies.id"), index=True)
    source_url: Mapped[str | None] = mapped_column(String(1000))
    source_type: Mapped[str] = mapped_column(String(120), nullable=False)
    ats_detected: Mapped[str] = mapped_column(String(120), default="Unknown")
    status: Mapped[str] = mapped_column(String(80), default="pending")
    http_status: Mapped[int | None] = mapped_column(Integer)
    checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_state: Mapped[str] = mapped_column(Text, default="")
    item_count: Mapped[int] = mapped_column(Integer, default=0)
    actor_name: Mapped[str | None] = mapped_column(String(200))
    actor_version: Mapped[str | None] = mapped_column(String(100))
    cost_estimate: Mapped[str | None] = mapped_column(String(100))
    last_run: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class WatchScanRun(TimestampMixin, Base):
    __tablename__ = "watch_scan_runs"

    tier: Mapped[str] = mapped_column(String(20), index=True)
    scan_type: Mapped[str] = mapped_column(String(80), default="manual")
    status: Mapped[str] = mapped_column(String(80), default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class JobOpportunity(TimestampMixin, Base):
    __tablename__ = "job_opportunities"
    __table_args__ = (Index("ix_job_company_title_location", "company_id", "title", "location"),)

    company_id: Mapped[str | None] = mapped_column(ForeignKey("companies.id"), index=True)
    title: Mapped[str] = mapped_column(String(250), nullable=False, index=True)
    location: Mapped[str | None] = mapped_column(String(250))
    country: Mapped[str | None] = mapped_column(String(120), index=True)
    work_mode: Mapped[str | None] = mapped_column(String(80))
    employment_type: Mapped[str | None] = mapped_column(String(80))
    source_url: Mapped[str | None] = mapped_column(String(1000))
    source_text: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[JobStatus] = mapped_column(String(50), default=JobStatus.DISCOVERED, index=True)
    extraction_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    missing_information: Mapped[list[str]] = mapped_column(JSON, default=list)

    company: Mapped[Company | None] = relationship()


class JobRequirement(TimestampMixin, Base):
    __tablename__ = "job_requirements"

    job_id: Mapped[str] = mapped_column(ForeignKey("job_opportunities.id"), index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, default=True)


class JobFitAssessment(TimestampMixin, Base):
    __tablename__ = "job_fit_assessments"

    job_id: Mapped[str] = mapped_column(ForeignKey("job_opportunities.id"), index=True)
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    recommendation: Mapped[str] = mapped_column(String(50), nullable=False)
    category_scores: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    explanation: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)


class SponsorshipAssessment(TimestampMixin, Base):
    __tablename__ = "sponsorship_assessments"

    job_id: Mapped[str] = mapped_column(ForeignKey("job_opportunities.id"), index=True)
    classification: Mapped[SponsorshipStatus] = mapped_column(String(80), nullable=False)
    evidence_fragment: Mapped[str] = mapped_column(Text, default="")
    source_url: Mapped[str | None] = mapped_column(String(1000))
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    human_reviewed: Mapped[bool] = mapped_column(Boolean, default=False)


class Contact(TimestampMixin, Base):
    __tablename__ = "contacts"

    company_id: Mapped[str | None] = mapped_column(ForeignKey("companies.id"), index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str | None] = mapped_column(String(200))
    channel: Mapped[str | None] = mapped_column(String(80))


class CVBaseVersion(TimestampMixin, Base):
    __tablename__ = "cv_base_versions"

    role_family_id: Mapped[str | None] = mapped_column(ForeignKey("role_families.id"), index=True)
    version: Mapped[str] = mapped_column(String(40), nullable=False)
    source_format: Mapped[str] = mapped_column(String(40), default="html")
    source_text: Mapped[str] = mapped_column(Text, default="")


class TailoredCV(TimestampMixin, Base):
    __tablename__ = "tailored_cvs"

    job_id: Mapped[str] = mapped_column(ForeignKey("job_opportunities.id"), index=True)
    base_cv_id: Mapped[str | None] = mapped_column(ForeignKey("cv_base_versions.id"), index=True)
    status: Mapped[str] = mapped_column(String(80), default="draft")
    source_text: Mapped[str] = mapped_column(Text, default="")
    rendered_pdf_path: Mapped[str | None] = mapped_column(String(1000))
    validation_summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class CoverLetter(TimestampMixin, Base):
    __tablename__ = "cover_letters"

    job_id: Mapped[str] = mapped_column(ForeignKey("job_opportunities.id"), index=True)
    status: Mapped[str] = mapped_column(String(80), default="draft")
    body: Mapped[str] = mapped_column(Text, default="")


class ApplicationQuestion(TimestampMixin, Base):
    __tablename__ = "application_questions"

    job_id: Mapped[str] = mapped_column(ForeignKey("job_opportunities.id"), index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    draft_answer: Mapped[str] = mapped_column(Text, default="")
    requires_review: Mapped[bool] = mapped_column(Boolean, default=True)


class Application(TimestampMixin, Base):
    __tablename__ = "applications"

    job_id: Mapped[str] = mapped_column(ForeignKey("job_opportunities.id"), index=True)
    status: Mapped[JobStatus] = mapped_column(String(50), default=JobStatus.AWAITING_REVIEW)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ApplicationEvent(TimestampMixin, Base):
    __tablename__ = "application_events"

    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="")


class Communication(TimestampMixin, Base):
    __tablename__ = "communications"

    application_id: Mapped[str | None] = mapped_column(ForeignKey("applications.id"), index=True)
    contact_id: Mapped[str | None] = mapped_column(ForeignKey("contacts.id"), index=True)
    channel: Mapped[str] = mapped_column(String(80), nullable=False)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="")


class Interview(TimestampMixin, Base):
    __tablename__ = "interviews"

    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id"), index=True)
    stage: Mapped[str] = mapped_column(String(100), nullable=False)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str] = mapped_column(Text, default="")


class InterviewPreparationPack(TimestampMixin, Base):
    __tablename__ = "interview_preparation_packs"

    interview_id: Mapped[str] = mapped_column(ForeignKey("interviews.id"), index=True)
    content: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    source_notes: Mapped[list[str]] = mapped_column(JSON, default=list)


class FollowUp(TimestampMixin, Base):
    __tablename__ = "follow_ups"

    application_id: Mapped[str | None] = mapped_column(ForeignKey("applications.id"), index=True)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="open")
    notes: Mapped[str] = mapped_column(Text, default="")


class Outcome(TimestampMixin, Base):
    __tablename__ = "outcomes"

    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id"), index=True)
    result: Mapped[str] = mapped_column(String(100), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(250))
    notes: Mapped[str] = mapped_column(Text, default="")


class WeeklyReport(TimestampMixin, Base):
    __tablename__ = "weekly_reports"

    week_start: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    facts: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    recommendations: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class AgentRun(TimestampMixin, Base):
    __tablename__ = "agent_runs"

    agent_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    input_summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    output_summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    provider: Mapped[str] = mapped_column(String(80), default="mock")
    status: Mapped[str] = mapped_column(String(80), default="succeeded")


class ValidationResult(TimestampMixin, Base):
    __tablename__ = "validation_results"

    subject_type: Mapped[str] = mapped_column(String(100), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(80), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class HumanApproval(TimestampMixin, Base):
    __tablename__ = "human_approvals"

    action_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    subject_type: Mapped[str] = mapped_column(String(100), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    status: Mapped[ApprovalStatus] = mapped_column(String(50), default=ApprovalStatus.REQUESTED)
    rationale: Mapped[str] = mapped_column(Text, default="")


class AuditEvent(TimestampMixin, Base):
    __tablename__ = "audit_events"

    actor: Mapped[str] = mapped_column(String(120), default="system")
    action: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    subject_type: Mapped[str] = mapped_column(String(100), nullable=False)
    subject_id: Mapped[str | None] = mapped_column(String(36), index=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
