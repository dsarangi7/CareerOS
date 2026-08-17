import pytest

from app.core.enums import ApprovalStatus, JobStatus
from app.models.entities import HumanApproval
from app.services.jobs import (
    ApprovalRequiredError,
    InvalidTransitionError,
    create_job,
    transition_job,
)


def test_invalid_status_transition_rejected(session) -> None:  # type: ignore[no-untyped-def]
    job = create_job(session, company_name="Example", title="Engineer")

    with pytest.raises(InvalidTransitionError):
        transition_job(session, job, JobStatus.APPLIED)


def test_approval_required_before_applied(session) -> None:  # type: ignore[no-untyped-def]
    job = create_job(session, company_name="Example", title="Engineer")
    transition_job(session, job, JobStatus.ASSESSED)
    transition_job(session, job, JobStatus.SHORTLISTED)
    transition_job(session, job, JobStatus.AWAITING_REVIEW)
    transition_job(session, job, JobStatus.READY_TO_APPLY)

    with pytest.raises(ApprovalRequiredError):
        transition_job(session, job, JobStatus.APPLIED)

    approval = HumanApproval(
        action_type="submit_application",
        subject_type="JobOpportunity",
        subject_id=job.id,
        status=ApprovalStatus.APPROVED,
    )
    session.add(approval)

    transition_job(session, job, JobStatus.APPLIED, approval=approval)
    assert job.status == JobStatus.APPLIED
