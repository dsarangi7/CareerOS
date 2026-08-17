from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from openpyxl import load_workbook
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entities import (
    Achievement,
    Application,
    ApplicationEvent,
    CandidateProfile,
    Communication,
    Company,
    Contact,
    FollowUp,
    Interview,
    InterviewPreparationPack,
    JobFitAssessment,
    JobOpportunity,
    JobRequirement,
    Outcome,
    SponsorshipAssessment,
    WeeklyReport,
)
from app.services.audit import record_audit


class ReportingError(ValueError):
    pass


def _require_application(session: Session, application_id: str) -> Application:
    application = session.get(Application, application_id)
    if application is None or application.deleted_at is not None:
        raise ReportingError("Application not found")
    return application


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def record_communication(
    session: Session,
    *,
    application_id: str,
    channel: str,
    direction: str,
    body: str = "",
    contact_id: str | None = None,
) -> Communication:
    _require_application(session, application_id)
    communication = Communication(
        application_id=application_id,
        contact_id=contact_id,
        channel=channel,
        direction=direction,
        body=body,
    )
    session.add(communication)
    session.flush()
    session.add(
        ApplicationEvent(
            application_id=application_id,
            event_type="communication_recorded",
            notes=f"{direction} {channel} communication logged locally.",
        )
    )
    record_audit(
        session,
        action="record_communication",
        subject_type="Communication",
        subject_id=communication.id,
        details={"application_id": application_id, "channel": channel, "direction": direction},
    )
    return communication


def schedule_follow_up(
    session: Session, *, application_id: str, due_at: datetime, notes: str = ""
) -> FollowUp:
    _require_application(session, application_id)
    follow_up = FollowUp(application_id=application_id, due_at=due_at, notes=notes, status="open")
    session.add(follow_up)
    session.flush()
    session.add(
        ApplicationEvent(
            application_id=application_id,
            event_type="follow_up_scheduled",
            notes=notes or "Follow-up scheduled.",
        )
    )
    record_audit(
        session,
        action="schedule_follow_up",
        subject_type="FollowUp",
        subject_id=follow_up.id,
        details={"application_id": application_id, "due_at": due_at.isoformat()},
    )
    return follow_up


def overdue_followups(session: Session, *, now: datetime | None = None) -> list[FollowUp]:
    current = now or datetime.now(UTC)
    rows = session.scalars(
        select(FollowUp).where(FollowUp.status == "open", FollowUp.deleted_at.is_(None))
    )
    return [row for row in rows if _aware(row.due_at) < _aware(current)]


def schedule_interview(
    session: Session,
    *,
    application_id: str,
    stage: str,
    scheduled_at: datetime | None = None,
    notes: str = "",
) -> Interview:
    _require_application(session, application_id)
    interview = Interview(
        application_id=application_id,
        stage=stage,
        scheduled_at=scheduled_at,
        notes=notes,
    )
    session.add(interview)
    session.flush()
    session.add(
        ApplicationEvent(
            application_id=application_id,
            event_type="interview_scheduled",
            notes=f"{stage} interview scheduled locally.",
        )
    )
    record_audit(
        session,
        action="schedule_interview",
        subject_type="Interview",
        subject_id=interview.id,
        details={"application_id": application_id, "stage": stage},
    )
    return interview


def generate_interview_prep_pack(
    session: Session, *, interview_id: str
) -> InterviewPreparationPack:
    interview = session.get(Interview, interview_id)
    if interview is None or interview.deleted_at is not None:
        raise ReportingError("Interview not found")
    application = _require_application(session, interview.application_id)
    job = session.get(JobOpportunity, application.job_id)
    if job is None:
        raise ReportingError("Interview job not found")
    company = session.get(Company, job.company_id) if job.company_id else None
    requirements = list(
        session.scalars(select(JobRequirement).where(JobRequirement.job_id == job.id))
    )
    profile = session.scalar(select(CandidateProfile).order_by(CandidateProfile.created_at))
    achievements = list(session.scalars(select(Achievement).limit(5)))
    requirement_text = [item.text for item in requirements[:8]]
    achievement_text = [item.title for item in achievements[:5]]
    company_name = company.name if company else "Unknown company"
    role_title = job.title
    content: dict[str, Any] = {
        "company_briefing": {
            "company": company_name,
            "note": (
                "Only locally stored company/job text is used; external company facts "
                "require source review."
            ),
        },
        "product_market_context": job.source_text[:700],
        "role_requirements": requirement_text,
        "likely_screening_questions": [
            f"Why are you interested in {role_title} at {company_name}?",
            "Which visa or relocation constraints should we know about?",
            "Which recent project best maps to this role?",
        ],
        "likely_technical_questions": [
            f"Explain your approach to {text.lower()}." for text in requirement_text[:5]
        ],
        "relevant_project_stories": achievement_text,
        "star_outlines": [
            {
                "situation": "Use a verified project or achievement from the profile.",
                "task": f"Map the story to {role_title} requirements.",
                "action": "Emphasize tools, constraints, and measurable decisions.",
                "result": "Use only verified or review-ready outcomes.",
            }
        ],
        "revision_plan": [
            "Confirm unsupported claims before interview use.",
            "Refresh salary, visa, and relocation preferences before recruiter screen.",
            "Add missing company facts only after reviewing trusted sources.",
        ],
        "questions_to_ask": [
            "What would success look like in the first 90 days?",
            "How is the team measuring battery/data engineering impact?",
            "What is the sponsorship or relocation process for this role?",
        ],
        "visa_relocation_salary": {
            "visa": "Discuss truthfully and keep country-specific authorization records current.",
            "relocation": profile.current_location if profile else "Confirm current location.",
            "salary": "Use compensation preference records before quoting a range.",
        },
        "thirty_sixty_ninety": {
            "30_days": "Understand data, product, and team workflows.",
            "60_days": "Ship a focused analysis or automation improvement.",
            "90_days": "Own a repeatable reporting or model-validation workflow.",
        },
    }
    pack = InterviewPreparationPack(
        interview_id=interview.id,
        content=content,
        source_notes=[
            "Generated from local profile, job description, requirements, and application records.",
            "No external web or recruiter system access was used.",
        ],
    )
    session.add(pack)
    session.flush()
    record_audit(
        session,
        action="generate_interview_prep_pack",
        subject_type="InterviewPreparationPack",
        subject_id=pack.id,
        details={"interview_id": interview.id},
    )
    return pack


def record_outcome(
    session: Session,
    *,
    application_id: str,
    result: str,
    reason: str | None = None,
    notes: str = "",
) -> Outcome:
    _require_application(session, application_id)
    outcome = Outcome(application_id=application_id, result=result, reason=reason, notes=notes)
    session.add(outcome)
    session.flush()
    session.add(
        ApplicationEvent(
            application_id=application_id,
            event_type="outcome_recorded",
            notes=f"Outcome recorded: {result}.",
        )
    )
    record_audit(
        session,
        action="record_outcome",
        subject_type="Outcome",
        subject_id=outcome.id,
        details={"application_id": application_id, "result": result},
    )
    return outcome


def generate_weekly_report(session: Session, *, week_start: str) -> WeeklyReport:
    job_count = session.scalar(select(func.count()).select_from(JobOpportunity)) or 0
    application_count = session.scalar(select(func.count()).select_from(Application)) or 0
    communication_count = session.scalar(select(func.count()).select_from(Communication)) or 0
    interview_count = session.scalar(select(func.count()).select_from(Interview)) or 0
    outcome_count = session.scalar(select(func.count()).select_from(Outcome)) or 0
    followups = list(session.scalars(select(FollowUp).where(FollowUp.deleted_at.is_(None))))
    overdue = overdue_followups(session)
    top_scores = session.execute(
        select(JobFitAssessment, JobOpportunity)
        .join(JobOpportunity, JobFitAssessment.job_id == JobOpportunity.id)
        .order_by(JobFitAssessment.total_score.desc())
        .limit(5)
    ).all()
    sponsorships = list(session.scalars(select(SponsorshipAssessment)))
    sponsorship_counter = Counter(str(item.classification) for item in sponsorships)
    skill_gaps: list[str] = []
    for score in session.scalars(select(JobFitAssessment)):
        missing = score.explanation.get("missing_requirements", [])
        if isinstance(missing, list):
            skill_gaps.extend(str(item) for item in missing[:5])
    facts: dict[str, Any] = {
        "new_jobs": job_count,
        "applications_total": application_count,
        "communications_total": communication_count,
        "interviews_total": interview_count,
        "outcomes_total": outcome_count,
        "followups_open": sum(1 for item in followups if item.status == "open"),
        "followups_overdue": len(overdue),
        "sponsorship_mix": dict(sponsorship_counter),
        "top_opportunities": [
            {
                "job_id": job.id,
                "title": job.title,
                "score": score.total_score,
                "recommendation": score.recommendation,
            }
            for score, job in top_scores
        ],
        "recurring_skill_gaps": Counter(skill_gaps).most_common(5),
    }
    recommendations = {
        "focus": [
            item["title"] for item in facts["top_opportunities"][:3] if isinstance(item, dict)
        ],
        "follow_up": "Clear overdue follow-ups before adding new outreach.",
        "risk": "Manually verify sponsorship, salary, and relocation assumptions before applying.",
    }
    report = WeeklyReport(week_start=week_start, facts=facts, recommendations=recommendations)
    session.add(report)
    session.flush()
    record_audit(
        session,
        action="generate_weekly_report",
        subject_type="WeeklyReport",
        subject_id=report.id,
        details={"week_start": week_start},
    )
    return report


def export_crm_workbook(session: Session, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    opportunities = session.execute(
        select(JobOpportunity, Company).join(Company, isouter=True)
    ).all()
    applications = list(session.scalars(select(Application)))
    contacts = list(session.scalars(select(Contact)))
    interviews = list(session.scalars(select(Interview)))
    followups = list(session.scalars(select(FollowUp)))
    outcomes = list(session.scalars(select(Outcome)))
    scores = list(session.scalars(select(JobFitAssessment)))
    weekly_reports = list(session.scalars(select(WeeklyReport)))
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        pd.DataFrame(
            [
                {
                    "Job ID": job.id,
                    "Company": company.name if company else "",
                    "Title": job.title,
                    "Country": job.country,
                    "Status": str(job.status),
                    "Source URL": job.source_url,
                }
                for job, company in opportunities
            ]
        ).to_excel(writer, sheet_name="Opportunity register", index=False)
        pd.DataFrame(
            [
                {
                    "Application ID": item.id,
                    "Job ID": item.job_id,
                    "Status": str(item.status),
                    "Applied at": _excel_value(item.applied_at),
                }
                for item in applications
            ]
        ).to_excel(writer, sheet_name="Application pipeline", index=False)
        pd.DataFrame(
            [
                {
                    "Contact ID": item.id,
                    "Name": item.name,
                    "Company ID": item.company_id,
                    "Role": item.role,
                    "Channel": item.channel,
                }
                for item in contacts
            ]
        ).to_excel(writer, sheet_name="Contacts", index=False)
        pd.DataFrame([_row_dict(item) for item in interviews]).to_excel(
            writer, sheet_name="Interviews", index=False
        )
        pd.DataFrame([_row_dict(item) for item in followups]).to_excel(
            writer, sheet_name="Follow-ups", index=False
        )
        pd.DataFrame([_row_dict(item) for item in outcomes]).to_excel(
            writer, sheet_name="Outcomes", index=False
        )
        pd.DataFrame(
            [
                {
                    "Job ID": score.job_id,
                    "Total score": score.total_score,
                    "Recommendation": score.recommendation,
                    "Confidence": score.confidence,
                    "Explanation": score.explanation,
                }
                for score in scores
            ]
        ).to_excel(writer, sheet_name="Skill-gap analysis", index=False)
        pd.DataFrame(
            [
                {
                    "Week start": report.week_start,
                    "Facts": report.facts,
                    "Recommendations": report.recommendations,
                }
                for report in weekly_reports
            ]
        ).to_excel(writer, sheet_name="Weekly summary", index=False)
        pd.DataFrame(
            [
                {"Field": "Opportunity register", "Definition": "Locally tracked job records."},
                {
                    "Field": "Application pipeline",
                    "Definition": "Human-controlled application status.",
                },
                {
                    "Field": "Follow-ups",
                    "Definition": "Open and completed follow-up reminders.",
                },
                {
                    "Field": "Weekly summary",
                    "Definition": "Stored weekly facts and recommendations.",
                },
            ]
        ).to_excel(writer, sheet_name="Data dictionary", index=False)
    _style_workbook(output_path)
    return output_path


def _row_dict(row: Any) -> dict[str, Any]:
    return {
        key: _excel_value(value) for key, value in row.__dict__.items() if not key.startswith("_")
    }


def _excel_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict | list):
        return str(value)
    return value


def _style_workbook(path: Path) -> None:
    workbook = load_workbook(path)
    for sheet in workbook.worksheets:
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
        for column in sheet.columns:
            values = [str(cell.value or "") for cell in column]
            width = min(max(max((len(value) for value in values), default=10) + 2, 12), 48)
            sheet.column_dimensions[column[0].column_letter].width = width
    workbook.save(path)
