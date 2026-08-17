from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import TypedDict

import pandas as pd
from sqlalchemy import func, select

from app.core.enums import JobStatus, SponsorshipStatus
from app.db.base import SessionLocal, create_all
from app.models.entities import (
    Application,
    AuditEvent,
    Company,
    FollowUp,
    Interview,
    JobFitAssessment,
    JobOpportunity,
    SponsorshipAssessment,
)
from app.scoring.fit import calculate_fit_score
from app.services.jobs import (
    assess_and_store_sponsorship,
    create_job,
    store_fit_assessment,
    transition_job,
)
from app.services.profile import seed_candidate_profile

ROOT = Path(__file__).resolve().parents[1]


class JobFixture(TypedDict):
    company: str
    title: str
    country: str
    text: str
    matched_skills: int
    required_skills: int
    matched_achievements: int


JOB_FIXTURES: list[JobFixture] = [
    {
        "company": "Maritime Cell Analytics",
        "title": "Battery Diagnostics Engineer",
        "country": "Netherlands",
        "text": (
            "Marine battery diagnostics role. Visa sponsorship may sponsor exceptional candidates."
        ),
        "matched_skills": 5,
        "required_skills": 6,
        "matched_achievements": 3,
    },
    {
        "company": "US Grid Batteries",
        "title": "Senior Battery Data Engineer",
        "country": "United States",
        "text": (
            "Battery analytics role. We are unable to sponsor visas and require US work "
            "authorization."
        ),
        "matched_skills": 5,
        "required_skills": 6,
        "matched_achievements": 3,
    },
    {
        "company": "Euro Industrial AI",
        "title": "Industrial AI Time-Series Engineer",
        "country": "Germany",
        "text": "Industrial AI, Python pipelines, anomaly detection, time-series analytics.",
        "matched_skills": 4,
        "required_skills": 6,
        "matched_achievements": 2,
    },
    {
        "company": "BMS Lab",
        "title": "BMS Data Analysis Engineer",
        "country": "United Kingdom",
        "text": "BMS data analysis, SOC, SOH, MATLAB, Python. Right to work required.",
        "matched_skills": 6,
        "required_skills": 7,
        "matched_achievements": 3,
    },
    {
        "company": "Cell Model Works",
        "title": "Battery Modelling Engineer",
        "country": "Sweden",
        "text": "Equivalent-circuit models, Simulink, SOC estimation, battery validation.",
        "matched_skills": 4,
        "required_skills": 6,
        "matched_achievements": 2,
    },
    {
        "company": "Knowledge Systems Co",
        "title": "RAG Engineer",
        "country": "Singapore",
        "text": "RAG systems, FAISS, embeddings, local LLM deployment, Python.",
        "matched_skills": 5,
        "required_skills": 5,
        "matched_achievements": 2,
    },
    {
        "company": "Scientific Compute Studio",
        "title": "Scientific Software Engineer",
        "country": "Canada",
        "text": "Scientific computing, data analysis, research software, Python.",
        "matched_skills": 4,
        "required_skills": 6,
        "matched_achievements": 2,
    },
    {
        "company": "Storage Market Analytics",
        "title": "Energy Storage Analyst",
        "country": "United Arab Emirates",
        "text": "Energy storage analysis, battery sizing, technical solutions, market context.",
        "matched_skills": 4,
        "required_skills": 5,
        "matched_achievements": 2,
    },
    {
        "company": "Defense Battery Systems",
        "title": "Battery Systems Engineer",
        "country": "United States",
        "text": "Battery systems role. Active security clearance and citizenship required.",
        "matched_skills": 6,
        "required_skills": 6,
        "matched_achievements": 3,
    },
    {
        "company": "Maritime Cell Analytics",
        "title": "Battery Diagnostics Engineer",
        "country": "Netherlands",
        "text": "Duplicate source for marine battery diagnostics. Sponsorship considered.",
        "matched_skills": 5,
        "required_skills": 6,
        "matched_achievements": 3,
    },
]


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def setup() -> None:
    create_all()
    (ROOT / "data" / "exports").mkdir(parents=True, exist_ok=True)


def migrate() -> None:
    create_all()


def seed() -> None:
    create_all()
    with SessionLocal() as session:
        seed_candidate_profile(session)
        existing_jobs = session.scalar(select(func.count()).select_from(JobOpportunity))
        if existing_jobs == 0:
            for fixture in JOB_FIXTURES:
                job = create_job(
                    session,
                    company_name=fixture["company"],
                    title=fixture["title"],
                    location="Hybrid",
                    country=fixture["country"],
                    source_text=fixture["text"],
                )
                sponsorship = assess_and_store_sponsorship(session, job)
                score = calculate_fit_score(
                    matched_skills=int(fixture["matched_skills"]),
                    required_skills=int(fixture["required_skills"]),
                    matched_achievements=int(fixture["matched_achievements"]),
                    relevant_domain="battery" in fixture["text"].lower()
                    or "rag" in fixture["text"].lower(),
                    seniority_aligned=True,
                    sponsorship_status=SponsorshipStatus(sponsorship.classification),
                    compensation_aligned=True,
                    strategic_value=True,
                )
                store_fit_assessment(
                    session,
                    job,
                    total_score=score["total_score"],
                    recommendation=str(score["recommendation"]),
                    category_scores=score["category_scores"],
                    explanation=dict(score["explanation"]),
                    confidence=score["confidence"],
                )
                transition_job(session, job, JobStatus.ASSESSED)
        session.commit()


def export_demo() -> Path:
    create_all()
    seed()
    output = ROOT / "data" / "exports" / "career_os_demo_export.xlsx"
    with SessionLocal() as session:
        opportunities = session.execute(
            select(JobOpportunity, Company).join(Company, isouter=True)
        ).all()
        scores = list(session.scalars(select(JobFitAssessment)))
        sponsorships = list(session.scalars(select(SponsorshipAssessment)))
        applications = list(session.scalars(select(Application)))
        interviews = list(session.scalars(select(Interview)))
        followups = list(session.scalars(select(FollowUp)))
        audit = list(session.scalars(select(AuditEvent)))

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame(
            [
                {
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
                    "Job ID": score.job_id,
                    "Total score": score.total_score,
                    "Recommendation": score.recommendation,
                    "Confidence": score.confidence,
                }
                for score in scores
            ]
        ).to_excel(writer, sheet_name="Skill-gap analysis", index=False)
        pd.DataFrame(
            [
                {
                    "Job ID": item.job_id,
                    "Classification": str(item.classification),
                    "Evidence": item.evidence_fragment,
                    "Confidence": item.confidence,
                }
                for item in sponsorships
            ]
        ).to_excel(writer, sheet_name="Weekly summary", index=False)
        pd.DataFrame([app.__dict__ for app in applications]).to_excel(
            writer, sheet_name="Application pipeline", index=False
        )
        pd.DataFrame(columns=["Name", "Company", "Role", "Channel"]).to_excel(
            writer, sheet_name="Contacts", index=False
        )
        pd.DataFrame([row.__dict__ for row in interviews]).to_excel(
            writer, sheet_name="Interviews", index=False
        )
        pd.DataFrame([row.__dict__ for row in followups]).to_excel(
            writer, sheet_name="Follow-ups", index=False
        )
        pd.DataFrame(columns=["Application ID", "Result", "Reason"]).to_excel(
            writer, sheet_name="Outcomes", index=False
        )
        pd.DataFrame(
            [
                {"Field": "Status", "Definition": "CareerOS application/job workflow status"},
                {"Field": "Recommendation", "Definition": "Explainable scoring decision band"},
            ]
        ).to_excel(writer, sheet_name="Data dictionary", index=False)
        pd.DataFrame([{"Audit events": len(audit), "Exported jobs": len(opportunities)}]).to_excel(
            writer, sheet_name="Summary metrics", index=False
        )
    return output


def validate() -> None:
    run([sys.executable, "-m", "ruff", "format", "--check", "."])
    run([sys.executable, "-m", "ruff", "check", "."])
    run([sys.executable, "-m", "mypy", "app", "scripts", "tests"])
    run([sys.executable, "-m", "pytest"])
    export_demo()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=["setup", "migrate", "seed", "validate", "export-demo"],
    )
    args = parser.parse_args()
    if args.command == "setup":
        setup()
    elif args.command == "migrate":
        migrate()
    elif args.command == "seed":
        seed()
    elif args.command == "validate":
        validate()
    elif args.command == "export-demo":
        output = export_demo()
        print(output)


if __name__ == "__main__":
    main()
