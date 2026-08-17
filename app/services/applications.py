from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import ApprovalStatus, JobStatus
from app.models.entities import Application, ApplicationEvent, HumanApproval, JobOpportunity
from app.services.audit import record_audit
from app.services.jobs import transition_job


class ApplicationWorkflowError(ValueError):
    pass


def shortlist_job(session: Session, job: JobOpportunity) -> JobOpportunity:
    if JobStatus(job.status) == JobStatus.DISCOVERED:
        transition_job(session, job, JobStatus.ASSESSED)
    if JobStatus(job.status) == JobStatus.ASSESSED:
        transition_job(session, job, JobStatus.SHORTLISTED)
    elif JobStatus(job.status) != JobStatus.SHORTLISTED:
        raise ApplicationWorkflowError(f"Cannot shortlist job from {job.status}")
    return job


def create_application_for_job(session: Session, job: JobOpportunity) -> Application:
    if JobStatus(job.status) == JobStatus.ASSESSED:
        shortlist_job(session, job)
    if JobStatus(job.status) == JobStatus.SHORTLISTED:
        transition_job(session, job, JobStatus.AWAITING_REVIEW)
    if JobStatus(job.status) != JobStatus.AWAITING_REVIEW:
        raise ApplicationWorkflowError(f"Cannot create application from {job.status}")
    existing = session.scalar(select(Application).where(Application.job_id == job.id))
    if existing is not None:
        return existing
    application = Application(job_id=job.id, status=JobStatus.AWAITING_REVIEW)
    session.add(application)
    session.flush()
    session.add(
        ApplicationEvent(
            application_id=application.id,
            event_type="application_created",
            notes="Draft application record created locally. No external action taken.",
        )
    )
    record_audit(
        session,
        action="create_application",
        subject_type="Application",
        subject_id=application.id,
        details={"job_id": job.id},
    )
    return application


def mark_ready_to_apply(session: Session, application: Application) -> Application:
    job = session.get(JobOpportunity, application.job_id)
    if job is None:
        raise ApplicationWorkflowError("Application job not found")
    if JobStatus(job.status) == JobStatus.AWAITING_REVIEW:
        transition_job(session, job, JobStatus.READY_TO_APPLY)
    if JobStatus(job.status) != JobStatus.READY_TO_APPLY:
        raise ApplicationWorkflowError(f"Cannot mark ready from {job.status}")
    application.status = JobStatus.READY_TO_APPLY
    session.add(
        ApplicationEvent(
            application_id=application.id,
            event_type="ready_to_apply",
            notes="Application marked ready for human-controlled submission.",
        )
    )
    return application


def mark_applied_with_approval(
    session: Session, application: Application, approval: HumanApproval
) -> Application:
    job = session.get(JobOpportunity, application.job_id)
    if job is None:
        raise ApplicationWorkflowError("Application job not found")
    if approval.status != ApprovalStatus.APPROVED:
        raise ApplicationWorkflowError("Approval must be approved")
    if approval.subject_id != job.id:
        raise ApplicationWorkflowError("Approval subject must match job")
    transition_job(session, job, JobStatus.APPLIED, approval=approval)
    application.status = JobStatus.APPLIED
    application.applied_at = datetime.now(UTC)
    session.add(
        ApplicationEvent(
            application_id=application.id,
            event_type="applied_simulated",
            notes="Application marked applied after local human approval record.",
        )
    )
    return application
