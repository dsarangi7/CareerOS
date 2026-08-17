from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import VerificationStatus
from app.models.entities import (
    Achievement,
    CandidateProfile,
    EducationRecord,
    EmploymentRecord,
    EvidenceRecord,
    Project,
    RoleFamily,
    Skill,
)
from app.services.audit import record_audit

CAREER_LANES = [
    "Battery Analytics and Diagnostics",
    "Battery Modelling and BMS Algorithms",
    "Industrial AI and Time-Series Analytics",
    "Engineering Software and Automation",
    "RAG and AI Knowledge Systems",
    "Energy Storage and Technical Solutions",
    "Scientific Data and Applied Research",
]

CAREER_THEMES = [
    "Marine lithium-ion battery systems",
    "Battery operational-data analytics",
    "SOC and SOH analysis",
    "Battery anomaly detection",
    "Battery diagnostics",
    "Python data pipelines",
    "MATLAB and Simulink",
    "RAG knowledge systems",
    "Local LLM deployment",
    "Engineering software tools",
    "BOM and engineering change workflows",
    "Scientific research and multidimensional data analysis",
]

PROJECTS = [
    "AYK Copilot RAG assistant",
    "FAISS-based retrieval",
    "BGE-M3 embeddings",
    "Local models including Qwen, Mistral, and MiniCPM variants",
    "Python analytics workflows",
    "Marine battery telematics analysis",
    "SOH reporting and calculation",
    "Voltage, temperature, and connection-resistance anomaly analysis",
    "Battery sizing Solution Tool",
    "BOM Engineering Workspace",
    "ECR and ERP workflow automation",
    "SolidWorks indented-BOM conversion",
    "SOC modelling work involving equivalent-circuit models",
    "MATLAB and Simulink development",
]


def seed_candidate_profile(session: Session) -> CandidateProfile:
    existing = session.scalar(
        select(CandidateProfile).where(CandidateProfile.name == "Dibya Jyoti Sarangi")
    )
    if existing:
        return existing

    profile = CandidateProfile(
        name="Dibya Jyoti Sarangi",
        current_location="Zhuhai, Guangdong, China",
        origin="Odisha, India",
        current_role="R&D Engineer at AYK Energy",
        positioning=(
            "Battery systems and R&D engineer combining marine battery analytics, operational "
            "data analysis, SOC/SOH development, AI/RAG systems, scientific computing, and "
            "engineering software automation."
        ),
        review_notes=(
            "Exact dates, degree wording, project ownership, fellowship dates, and metrics require "
            "confirmation before use as finalized CV claims."
        ),
    )
    session.add(profile)
    session.flush()

    session.add(
        EmploymentRecord(
            profile_id=profile.id,
            employer="AYK Energy",
            title="R&D Engineer",
            location="Zhuhai, Guangdong, China",
            verification_status=VerificationStatus.USER_REPORTED_PENDING_EVIDENCE,
            notes="Seeded from user prompt; dates and exact title wording require confirmation.",
        )
    )

    for degree, institution, field in [
        ("B.Sc.", "Institution requires confirmation", "Physics"),
        ("M.Sc. or Applied Science qualification", "Institution requires confirmation", None),
        ("M.Tech", "IIT Delhi", "Applied Optics"),
    ]:
        session.add(
            EducationRecord(
                profile_id=profile.id,
                institution=institution,
                degree=degree,
                field=field,
                verification_status=VerificationStatus.REQUIRES_CONFIRMATION,
            )
        )

    for lane in CAREER_LANES:
        session.add(RoleFamily(name=lane, description=f"Initial career lane: {lane}"))

    for theme in CAREER_THEMES:
        session.add(
            Skill(
                profile_id=profile.id,
                name=theme,
                category="career_theme",
                verification_status=VerificationStatus.USER_REPORTED_PENDING_EVIDENCE,
            )
        )

    for name in PROJECTS:
        project = Project(
            profile_id=profile.id,
            name=name,
            summary="Seeded as known technical work; scope and ownership require evidence review.",
            verification_status=VerificationStatus.USER_REPORTED_PENDING_EVIDENCE,
        )
        session.add(project)
        achievement = Achievement(
            profile_id=profile.id,
            title=name,
            description="Synthetic demonstration achievement pending evidence attachment.",
            verification_status=VerificationStatus.USER_REPORTED_PENDING_EVIDENCE,
            evidence_strength="seed_only",
        )
        session.add(achievement)
        session.flush()
        session.add(
            EvidenceRecord(
                achievement_id=achievement.id,
                title=f"Seed note for {name}",
                source_type="seed_prompt",
                source_ref="Initial user-provided CareerOS brief.",
                verification_status=VerificationStatus.REQUIRES_CONFIRMATION,
            )
        )

    record_audit(
        session, action="seed_profile", subject_type="CandidateProfile", subject_id=profile.id
    )
    return profile
