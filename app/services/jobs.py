from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import ApprovalStatus, JobStatus, SponsorshipStatus
from app.models.entities import (
    Company,
    HumanApproval,
    JobFitAssessment,
    JobOpportunity,
    SponsorshipAssessment,
)
from app.services.audit import record_audit

ALLOWED_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    JobStatus.DISCOVERED: {JobStatus.ASSESSED, JobStatus.ARCHIVED},
    JobStatus.ASSESSED: {JobStatus.SHORTLISTED, JobStatus.ARCHIVED, JobStatus.REJECTED},
    JobStatus.SHORTLISTED: {JobStatus.CV_DRAFTING, JobStatus.AWAITING_REVIEW, JobStatus.ARCHIVED},
    JobStatus.CV_DRAFTING: {JobStatus.AWAITING_REVIEW, JobStatus.ARCHIVED},
    JobStatus.AWAITING_REVIEW: {JobStatus.READY_TO_APPLY, JobStatus.ARCHIVED},
    JobStatus.READY_TO_APPLY: {JobStatus.APPLIED, JobStatus.WITHDRAWN, JobStatus.ARCHIVED},
    JobStatus.APPLIED: {JobStatus.RECRUITER_CONTACT, JobStatus.REJECTED, JobStatus.WITHDRAWN},
    JobStatus.RECRUITER_CONTACT: {JobStatus.SCREENING, JobStatus.REJECTED, JobStatus.WITHDRAWN},
    JobStatus.SCREENING: {JobStatus.TECHNICAL_INTERVIEW, JobStatus.REJECTED, JobStatus.WITHDRAWN},
    JobStatus.TECHNICAL_INTERVIEW: {
        JobStatus.HIRING_MANAGER_INTERVIEW,
        JobStatus.FINAL_INTERVIEW,
        JobStatus.REJECTED,
        JobStatus.WITHDRAWN,
    },
    JobStatus.HIRING_MANAGER_INTERVIEW: {
        JobStatus.FINAL_INTERVIEW,
        JobStatus.OFFER,
        JobStatus.REJECTED,
    },
    JobStatus.FINAL_INTERVIEW: {JobStatus.OFFER, JobStatus.REJECTED},
    JobStatus.OFFER: {JobStatus.ACCEPTED, JobStatus.REJECTED, JobStatus.WITHDRAWN},
    JobStatus.ACCEPTED: {JobStatus.ARCHIVED},
    JobStatus.REJECTED: {JobStatus.ARCHIVED},
    JobStatus.WITHDRAWN: {JobStatus.ARCHIVED},
    JobStatus.ARCHIVED: set(),
}

APPROVAL_REQUIRED = {
    JobStatus.APPLIED,
    JobStatus.WITHDRAWN,
    JobStatus.ACCEPTED,
    JobStatus.REJECTED,
}


class InvalidTransitionError(ValueError):
    pass


class ApprovalRequiredError(PermissionError):
    pass


def create_job(
    session: Session,
    *,
    company_name: str,
    title: str,
    location: str | None = None,
    country: str | None = None,
    source_url: str | None = None,
    source_text: str = "",
) -> JobOpportunity:
    company = session.scalar(select(Company).where(Company.name == company_name))
    if company is None:
        company = Company(name=company_name)
        session.add(company)
        session.flush()

    job = JobOpportunity(
        company_id=company.id,
        title=title,
        location=location,
        country=country,
        source_url=source_url,
        source_text=source_text,
        extraction_confidence=0.65 if source_text else 0.2,
        missing_information=[] if location and country else ["location_or_country"],
    )
    session.add(job)
    session.flush()
    record_audit(session, action="create_job", subject_type="JobOpportunity", subject_id=job.id)
    return job


def classify_sponsorship(source_text: str, source_url: str | None = None) -> SponsorshipAssessment:
    text = source_text.lower()
    rules: list[tuple[SponsorshipStatus, list[str], float]] = [
        (
            SponsorshipStatus.SECURITY_CLEARANCE_REQUIRED,
            ["security clearance", "active clearance"],
            0.95,
        ),
        (
            SponsorshipStatus.CITIZENSHIP_REQUIRED,
            ["citizenship required", "citizen required"],
            0.95,
        ),
        (
            SponsorshipStatus.EXPLICITLY_UNAVAILABLE,
            ["no sponsorship", "unable to sponsor", "will not sponsor"],
            0.95,
        ),
        (
            SponsorshipStatus.REQUIRES_EXISTING_WORK_AUTHORIZATION,
            ["must already be authorized", "existing work authorization", "right to work"],
            0.9,
        ),
        (
            SponsorshipStatus.EXPLICITLY_AVAILABLE,
            ["visa sponsorship available", "sponsorship is available", "will sponsor"],
            0.95,
        ),
        (SponsorshipStatus.POSSIBLY_AVAILABLE, ["may sponsor", "sponsorship considered"], 0.65),
    ]
    for status, phrases, confidence in rules:
        for phrase in phrases:
            if phrase in text:
                return SponsorshipAssessment(
                    job_id="",
                    classification=status,
                    evidence_fragment=phrase,
                    source_url=source_url,
                    confidence=confidence,
                )
    return SponsorshipAssessment(
        job_id="",
        classification=SponsorshipStatus.NOT_MENTIONED,
        evidence_fragment="",
        source_url=source_url,
        confidence=0.8,
    )


def transition_job(
    session: Session,
    job: JobOpportunity,
    target: JobStatus,
    *,
    approval: HumanApproval | None = None,
) -> JobOpportunity:
    current = JobStatus(job.status)
    if target not in ALLOWED_TRANSITIONS[current]:
        raise InvalidTransitionError(
            f"Cannot transition job from {current.value} to {target.value}"
        )
    if target in APPROVAL_REQUIRED and (
        approval is None
        or approval.status != ApprovalStatus.APPROVED
        or approval.subject_id != job.id
    ):
        raise ApprovalRequiredError(f"Human approval is required before {target.value}")

    job.status = target
    record_audit(
        session,
        action="transition_job",
        subject_type="JobOpportunity",
        subject_id=job.id,
        details={"from": current.value, "to": target.value},
    )
    return job


def assess_and_store_sponsorship(session: Session, job: JobOpportunity) -> SponsorshipAssessment:
    assessment = classify_sponsorship(job.source_text, job.source_url)
    assessment.job_id = job.id
    session.add(assessment)
    record_audit(
        session,
        action="classify_sponsorship",
        subject_type="JobOpportunity",
        subject_id=job.id,
        details={"classification": assessment.classification.value},
    )
    return assessment


def store_fit_assessment(
    session: Session,
    job: JobOpportunity,
    *,
    total_score: float,
    recommendation: str,
    category_scores: dict[str, float],
    explanation: dict[str, object],
    confidence: float,
) -> JobFitAssessment:
    assessment = JobFitAssessment(
        job_id=job.id,
        total_score=total_score,
        recommendation=recommendation,
        category_scores=category_scores,
        explanation=explanation,
        confidence=confidence,
    )
    session.add(assessment)
    record_audit(session, action="score_job", subject_type="JobOpportunity", subject_id=job.id)
    return assessment
