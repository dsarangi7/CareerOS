from app.core.enums import ApprovalStatus, JobStatus
from app.models.entities import HumanApproval
from app.services.applications import (
    create_application_for_job,
    mark_applied_with_approval,
    mark_ready_to_apply,
    shortlist_job,
)
from app.services.jobs import ingest_job_description

JOB_TEXT = """
Company: Applied Workflow Energy
Title: Battery Analytics Engineer
Country: Netherlands
Required: Python and battery diagnostics experience.
Visa sponsorship may sponsor exceptional candidates.
"""


def test_application_workflow_requires_local_approval_before_applied(session) -> None:  # type: ignore[no-untyped-def]
    job, *_ = ingest_job_description(session, source_text=JOB_TEXT)
    shortlist_job(session, job)
    application = create_application_for_job(session, job)
    mark_ready_to_apply(session, application)
    approval = HumanApproval(
        action_type="submit_application",
        subject_type="JobOpportunity",
        subject_id=job.id,
        status=ApprovalStatus.APPROVED,
        rationale="Simulated approval for test.",
    )
    session.add(approval)
    session.flush()
    mark_applied_with_approval(session, application, approval)

    assert job.status == JobStatus.APPLIED
    assert application.status == JobStatus.APPLIED
    assert application.applied_at is not None
