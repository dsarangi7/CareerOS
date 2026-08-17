from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import ApprovalStatus, VerificationStatus
from app.models.entities import (
    Achievement,
    CandidateProfile,
    CVBaseVersion,
    EvidenceRecord,
    HumanApproval,
    JobOpportunity,
    Skill,
    TailoredCV,
    ValidationResult,
)
from app.services.audit import record_audit

EXPORT_DIR = Path("data/exports/cv")


class CVGenerationError(ValueError):
    pass


def generate_tailored_cv(
    session: Session,
    *,
    profile_id: str,
    job_id: str,
    base_version: str = "battery-analytics-v1",
    output_dir: Path = EXPORT_DIR,
) -> TailoredCV:
    profile = session.get(CandidateProfile, profile_id)
    job = session.get(JobOpportunity, job_id)
    if profile is None:
        raise CVGenerationError("Profile not found")
    if job is None:
        raise CVGenerationError("Job not found")
    base_cv = _get_or_create_base_cv(session, base_version)
    supported_claims = _supported_claims(session, profile_id)
    unsupported_claims = _unsupported_claims(session, job, supported_claims)
    required_confirmation = [
        "Confirm exact dates, formal titles, metrics, and ownership before external use."
    ]
    html = _render_html(profile, job, supported_claims, unsupported_claims)
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"{job.id}_tailored_cv.pdf"
    _render_pdf(profile, job, supported_claims, unsupported_claims, pdf_path)
    readable = validate_pdf_text(pdf_path)
    status = "draft_blocked" if unsupported_claims else "draft_awaiting_review"
    summary: dict[str, object] = {
        "supported_claims": supported_claims,
        "unsupported_claims": unsupported_claims,
        "required_user_confirmation": required_confirmation,
        "pdf_text_readable": readable,
        "finalization_blocked": bool(unsupported_claims),
    }
    tailored = TailoredCV(
        job_id=job.id,
        base_cv_id=base_cv.id,
        status=status,
        source_text=html,
        rendered_pdf_path=str(pdf_path),
        validation_summary=summary,
    )
    session.add(tailored)
    session.flush()
    session.add(
        ValidationResult(
            subject_type="TailoredCV",
            subject_id=tailored.id,
            status="blocked" if unsupported_claims else "passed_with_review_required",
            details=summary,
        )
    )
    session.add(
        HumanApproval(
            action_type="publish_cv",
            subject_type="TailoredCV",
            subject_id=tailored.id,
            status=ApprovalStatus.REQUESTED,
            rationale="Human review required before sharing or publishing this CV.",
        )
    )
    record_audit(
        session,
        action="generate_tailored_cv",
        subject_type="TailoredCV",
        subject_id=tailored.id,
        details={"job_id": job.id, "status": status},
    )
    return tailored


def validate_pdf_text(pdf_path: Path) -> bool:
    reader = PdfReader(str(pdf_path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return "Dibya Jyoti Sarangi" in text and len(text.strip()) > 100


def _get_or_create_base_cv(session: Session, version: str) -> CVBaseVersion:
    existing = session.scalar(select(CVBaseVersion).where(CVBaseVersion.version == version))
    if existing is not None:
        return existing
    base = CVBaseVersion(
        version=version,
        source_format="html",
        source_text="<html><body>{{ tailored_cv }}</body></html>",
    )
    session.add(base)
    session.flush()
    return base


def _supported_claims(session: Session, profile_id: str) -> list[dict[str, object]]:
    achievements = list(
        session.scalars(
            select(Achievement).where(
                Achievement.profile_id == profile_id,
                Achievement.deleted_at.is_(None),
                Achievement.verification_status == VerificationStatus.VERIFIED,
            )
        )
    )
    claims: list[dict[str, object]] = []
    for achievement in achievements:
        evidence = session.scalar(
            select(EvidenceRecord)
            .where(EvidenceRecord.achievement_id == achievement.id)
            .order_by(EvidenceRecord.created_at.desc())
        )
        claims.append(
            {
                "cv_sentence": achievement.description or achievement.title,
                "achievement_id": achievement.id,
                "achievement": achievement.title,
                "evidence_record_id": evidence.id if evidence else None,
                "evidence_strength": achievement.evidence_strength,
                "verification_status": VerificationStatus.VERIFIED.value,
                "risk": "low" if evidence else "medium_no_evidence_record",
            }
        )
    return claims


def _unsupported_claims(
    session: Session, job: JobOpportunity, supported_claims: list[dict[str, object]]
) -> list[str]:
    supported_text = " ".join(str(claim["cv_sentence"]).lower() for claim in supported_claims)
    skills = list(session.scalars(select(Skill).where(Skill.deleted_at.is_(None))))
    verified_skill_text = " ".join(
        skill.name.lower()
        for skill in skills
        if skill.verification_status == VerificationStatus.VERIFIED
    )
    required_terms = [
        term
        for term in ["python", "battery", "bms", "soc", "soh", "rag", "faiss", "matlab"]
        if term in job.source_text.lower()
    ]
    return [
        f"No verified evidence found for job keyword: {term}"
        for term in sorted(set(required_terms))
        if term not in supported_text and term not in verified_skill_text
    ]


def _render_html(
    profile: CandidateProfile,
    job: JobOpportunity,
    supported_claims: list[dict[str, object]],
    unsupported_claims: list[str],
) -> str:
    claims_html = "\n".join(
        f"<li>{escape(str(claim['cv_sentence']))}</li>" for claim in supported_claims
    )
    risks_html = "\n".join(f"<li>{escape(item)}</li>" for item in unsupported_claims)
    return f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>Tailored CV Draft</title></head>
<body>
<h1>{escape(profile.name)}</h1>
<p>{escape(profile.positioning)}</p>
<h2>Target Role</h2>
<p>{escape(job.title)} - {escape(job.country or job.location or "Location not specified")}</p>
<h2>Verified Relevant Evidence</h2>
<ul>{claims_html}</ul>
<h2>Validation Risks</h2>
<ul>{risks_html}</ul>
</body>
</html>"""


def _render_pdf(
    profile: CandidateProfile,
    job: JobOpportunity,
    supported_claims: list[dict[str, object]],
    unsupported_claims: list[str],
    pdf_path: Path,
) -> None:
    pdf = canvas.Canvas(str(pdf_path), pagesize=A4)
    width, height = A4
    y = height - 50
    for line in [
        profile.name,
        profile.positioning,
        f"Target role: {job.title}",
        f"Location: {job.country or job.location or 'Not specified'}",
        "Verified relevant evidence:",
    ]:
        y = _draw_wrapped(pdf, line, 50, y, width - 100)
    for claim in supported_claims:
        y = _draw_wrapped(pdf, f"- {claim['cv_sentence']}", 60, y, width - 120)
    y = _draw_wrapped(pdf, "Validation risks:", 50, y - 10, width - 100)
    for risk in unsupported_claims or ["No unsupported material claims detected."]:
        y = _draw_wrapped(pdf, f"- {risk}", 60, y, width - 120)
    pdf.save()


def _draw_wrapped(pdf: canvas.Canvas, text: str, x: float, y: float, max_width: float) -> float:
    words = text.split()
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if pdf.stringWidth(candidate, "Helvetica", 10) <= max_width:
            line = candidate
            continue
        pdf.drawString(x, y, line)
        y -= 14
        line = word
    if line:
        pdf.drawString(x, y, line)
        y -= 14
    if y < 60:
        pdf.showPage()
        y = A4[1] - 50
    return y
