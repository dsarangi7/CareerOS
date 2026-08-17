import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import ApprovalStatus, JobStatus, SponsorshipStatus
from app.models.entities import (
    Company,
    HumanApproval,
    JobFitAssessment,
    JobOpportunity,
    JobRequirement,
    SponsorshipAssessment,
)
from app.scoring.fit import calculate_fit_score
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


class JobNotFoundError(LookupError):
    pass


TECHNICAL_KEYWORDS = [
    "python",
    "matlab",
    "simulink",
    "battery",
    "bms",
    "soc",
    "soh",
    "rag",
    "faiss",
    "embeddings",
    "time-series",
    "anomaly",
    "diagnostics",
    "modelling",
    "modeling",
]


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


def ingest_job_description(
    session: Session,
    *,
    source_text: str,
    source_url: str | None = None,
    default_company: str = "Unknown Company",
    default_title: str = "Untitled Role",
) -> tuple[
    JobOpportunity, str | None, list[JobRequirement], SponsorshipAssessment, JobFitAssessment
]:
    extracted = extract_job_fields(source_text)
    company_name = extracted.get("company") or default_company
    title = extracted.get("title") or default_title
    location = extracted.get("location")
    country = extracted.get("country")
    duplicate = find_duplicate_job(
        session,
        company_name=company_name,
        title=title,
        source_url=source_url,
    )
    job = create_job(
        session,
        company_name=company_name,
        title=title,
        location=location,
        country=country,
        source_url=source_url,
        source_text=source_text,
    )
    requirements = store_extracted_requirements(session, job, source_text)
    sponsorship = assess_and_store_sponsorship(session, job)
    matched_skills = count_keyword_matches(source_text)
    score = calculate_fit_score(
        matched_skills=matched_skills,
        required_skills=max(len(requirements), 1),
        matched_achievements=min(3, matched_skills // 2),
        relevant_domain=any(term in source_text.lower() for term in ["battery", "bms", "rag"]),
        seniority_aligned=not _contains_any(source_text, ["director", "vp ", "principal"]),
        sponsorship_status=SponsorshipStatus(sponsorship.classification),
        compensation_aligned=True,
        strategic_value=any(
            term in source_text.lower()
            for term in ["battery", "diagnostics", "time-series", "rag", "scientific"]
        ),
    )
    fit = store_fit_assessment(
        session,
        job,
        total_score=score["total_score"],
        recommendation=str(score["recommendation"]),
        category_scores=score["category_scores"],
        explanation=dict(score["explanation"])
        | {"duplicate_of": duplicate.id if duplicate is not None else None},
        confidence=score["confidence"],
    )
    transition_job(session, job, JobStatus.ASSESSED)
    return job, duplicate.id if duplicate is not None else None, requirements, sponsorship, fit


def extract_job_fields(source_text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    patterns = {
        "company": r"(?:company|employer)\s*:\s*(?P<value>.+)",
        "title": r"(?:title|role)\s*:\s*(?P<value>.+)",
        "location": r"location\s*:\s*(?P<value>.+)",
        "country": r"country\s*:\s*(?P<value>.+)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, source_text, flags=re.IGNORECASE)
        if match:
            fields[key] = match.group("value").strip().splitlines()[0][:250]
    return fields


def store_extracted_requirements(
    session: Session, job: JobOpportunity, source_text: str
) -> list[JobRequirement]:
    requirements: list[JobRequirement] = []
    lines = [line.strip(" -*\t") for line in source_text.splitlines() if line.strip()]
    for line in lines:
        lowered = line.lower()
        if any(marker in lowered for marker in ["required", "must", "experience", "skill"]):
            requirement = JobRequirement(
                job_id=job.id,
                category=_requirement_category(line),
                text=line[:1000],
                required=not any(marker in lowered for marker in ["preferred", "nice to have"]),
            )
            session.add(requirement)
            requirements.append(requirement)
    if not requirements:
        for keyword in sorted(set(_matched_keywords(source_text))):
            requirement = JobRequirement(
                job_id=job.id,
                category="skill",
                text=f"Mentions {keyword}",
                required=True,
            )
            session.add(requirement)
            requirements.append(requirement)
    session.flush()
    record_audit(
        session,
        action="extract_job_requirements",
        subject_type="JobOpportunity",
        subject_id=job.id,
        details={"requirement_count": len(requirements)},
    )
    return requirements


def find_duplicate_job(
    session: Session, *, company_name: str, title: str, source_url: str | None
) -> JobOpportunity | None:
    company = session.scalar(
        select(Company).where(func.lower(Company.name) == company_name.lower())
    )
    if company is None:
        return None
    query = select(JobOpportunity).where(
        JobOpportunity.company_id == company.id,
        func.lower(JobOpportunity.title) == title.lower(),
        JobOpportunity.deleted_at.is_(None),
    )
    if source_url:
        url_duplicate = session.scalar(
            select(JobOpportunity).where(JobOpportunity.source_url == source_url)
        )
        if url_duplicate is not None:
            return url_duplicate
    return session.scalar(query)


def count_keyword_matches(source_text: str) -> int:
    return len(set(_matched_keywords(source_text)))


def _matched_keywords(source_text: str) -> list[str]:
    text = source_text.lower()
    return [keyword for keyword in TECHNICAL_KEYWORDS if keyword in text]


def _contains_any(source_text: str, needles: list[str]) -> bool:
    text = source_text.lower()
    return any(needle in text for needle in needles)


def _requirement_category(line: str) -> str:
    lowered = line.lower()
    if any(term in lowered for term in ["visa", "work authorization", "citizen", "clearance"]):
        return "eligibility"
    if any(term in lowered for term in ["python", "matlab", "simulink", "bms", "battery"]):
        return "technical_skill"
    if "language" in lowered:
        return "language"
    return "requirement"


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
