from pathlib import Path

from sqlalchemy import select

from app.core.enums import VerificationStatus
from app.document_generation.cv import generate_tailored_cv, validate_pdf_text
from app.models.entities import Achievement, HumanApproval, TailoredCV
from app.schemas.evidence import AchievementCreate, EvidenceRecordCreate, SkillCreate
from app.services.evidence import create_achievement, create_evidence, create_skill
from app.services.jobs import ingest_job_description
from app.services.profile import seed_candidate_profile

JOB_TEXT = """
Company: CV Battery Co
Title: Battery Diagnostics Engineer
Country: Germany
Required: Python, battery diagnostics, BMS, SOC and SOH experience.
Visa sponsorship may sponsor exceptional candidates.
"""


def test_tailored_cv_generation_claim_validation_and_pdf(session, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    profile = seed_candidate_profile(session)
    skill = create_skill(
        session,
        profile.id,
        SkillCreate(
            name="Python battery diagnostics", verification_status=VerificationStatus.VERIFIED
        ),
    )
    achievement = create_achievement(
        session,
        profile.id,
        AchievementCreate(
            title="Verified SOH analytics workflow",
            description=(
                "Built verified Python battery diagnostics workflow for SOC and SOH analysis."
            ),
            verification_status=VerificationStatus.VERIFIED,
            evidence_strength="strong",
        ),
    )
    evidence = create_evidence(
        session,
        EvidenceRecordCreate(
            achievement_id=achievement.id,
            title="Verified test evidence",
            source_type="test_fixture",
            source_ref="tests/integration/test_phase4_cv_generation.py",
            verification_status=VerificationStatus.VERIFIED,
        ),
    )
    job, *_ = ingest_job_description(session, source_text=JOB_TEXT)
    tailored = generate_tailored_cv(
        session,
        profile_id=profile.id,
        job_id=job.id,
        output_dir=tmp_path,
    )
    session.commit()

    assert skill.id
    assert evidence.id
    assert tailored.status in {"draft_awaiting_review", "draft_blocked"}
    assert tailored.rendered_pdf_path is not None
    assert validate_pdf_text(Path(tailored.rendered_pdf_path))
    assert tailored.validation_summary["supported_claims"]
    assert session.scalar(select(TailoredCV).where(TailoredCV.id == tailored.id)) is not None
    assert (
        session.scalar(
            select(HumanApproval).where(
                HumanApproval.subject_type == "TailoredCV",
                HumanApproval.subject_id == tailored.id,
            )
        )
        is not None
    )
    assert session.scalar(select(Achievement).where(Achievement.id == achievement.id)) is not None
