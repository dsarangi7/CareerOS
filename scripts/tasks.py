from __future__ import annotations

import argparse
import py_compile
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TypedDict

from sqlalchemy import func, select

from app.core.enums import JobStatus, SponsorshipStatus
from app.db.base import SessionLocal, create_all
from app.models.entities import (
    CandidateProfile,
    JobOpportunity,
)
from app.scoring.fit import calculate_fit_score
from app.security.hardening import create_sqlite_backup, scan_repo_for_secrets
from app.services.job_import import import_jobs_from_file
from app.services.jobs import (
    assess_and_store_sponsorship,
    create_job,
    store_fit_assessment,
    transition_job,
)
from app.services.profile import seed_candidate_profile
from app.services.profile_io import export_profile_csv_bundle, export_profile_workbook
from app.services.reporting import export_crm_workbook

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
        return export_crm_workbook(session, output)


def export_profile() -> Path:
    create_all()
    seed()
    output = ROOT / "data" / "exports" / "career_os_profile_export.xlsx"
    with SessionLocal() as session:
        profile = session.scalar(select(CandidateProfile).order_by(CandidateProfile.created_at))
        if profile is None:
            raise RuntimeError("Seed profile not found")
        return export_profile_workbook(session, profile.id, output)


def export_profile_csv() -> Path:
    create_all()
    seed()
    output = ROOT / "data" / "exports" / "career_os_profile_csv"
    with SessionLocal() as session:
        profile = session.scalar(select(CandidateProfile).order_by(CandidateProfile.created_at))
        if profile is None:
            raise RuntimeError("Seed profile not found")
        return export_profile_csv_bundle(session, profile.id, output)


def validate() -> None:
    run([sys.executable, "-m", "ruff", "format", "--check", "."])
    run([sys.executable, "-m", "ruff", "check", "."])
    run([sys.executable, "-m", "mypy", "app", "scripts", "tests"])
    run([sys.executable, "-m", "pytest"])
    security_scan()
    api_smoke()
    dashboard_smoke()
    docker_check()
    export_demo()
    export_profile()
    export_profile_csv()


def security_scan() -> None:
    findings = scan_repo_for_secrets(ROOT)
    if findings:
        for path, match_types in findings.items():
            print(f"{path}: {', '.join(match_types)}")
        raise SystemExit("Potential secret material found")
    print("Security scan passed: no obvious secret patterns found.")


def backup_db() -> Path:
    db_path = ROOT / "career_os.db"
    output_dir = ROOT / "data" / "backups"
    return create_sqlite_backup(db_path, output_dir)


def api_smoke() -> None:
    from fastapi.testclient import TestClient

    from app.api.main import app

    response = TestClient(app).get("/health")
    if response.status_code != 200 or response.json().get("status") != "ok":
        raise SystemExit("API smoke check failed")
    print("API smoke check passed.")


def dashboard_smoke() -> None:
    required_pages = {
        "01_Opportunities.py",
        "02_Career_Profile.py",
        "03_Review_Queue.py",
        "04_Achievements_and_Evidence.py",
        "05_CV_Library.py",
        "06_Applications_Pipeline.py",
        "07_Communications.py",
        "08_Interviews.py",
        "09_Follow-ups.py",
        "10_Weekly_Reports.py",
        "11_Analytics.py",
        "12_Settings.py",
        "13_Opportunity_Detail.py",
    }
    pages_dir = ROOT / "dashboard" / "pages"
    actual_pages = {path.name for path in pages_dir.glob("*.py")}
    missing = required_pages - actual_pages
    if missing:
        raise SystemExit(f"Dashboard pages missing: {sorted(missing)}")
    py_compile.compile(str(ROOT / "dashboard" / "Home.py"), doraise=True)
    for path in pages_dir.glob("*.py"):
        py_compile.compile(str(path), doraise=True)
    print("Dashboard smoke check passed.")


def docker_check() -> None:
    required_files = [ROOT / "Dockerfile", ROOT / "docker-compose.yml"]
    missing = [str(path.name) for path in required_files if not path.exists()]
    if missing:
        raise SystemExit(f"Docker files missing: {missing}")
    if shutil.which("docker") is None:
        print("Docker executable not found; Docker startup check skipped on this machine.")
        return
    run(["docker", "compose", "config"])
    print("Docker compose configuration check passed.")


def import_jobs(path: Path) -> None:
    create_all()
    with SessionLocal() as session:
        summary = import_jobs_from_file(session, path)
        session.commit()
    print(summary)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=[
            "setup",
            "migrate",
            "seed",
            "validate",
            "export-demo",
            "export-profile",
            "export-profile-csv",
            "import-jobs",
            "security-scan",
            "backup-db",
            "api-smoke",
            "dashboard-smoke",
            "docker-check",
        ],
    )
    parser.add_argument("--path", type=Path)
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
    elif args.command == "export-profile":
        output = export_profile()
        print(output)
    elif args.command == "export-profile-csv":
        output = export_profile_csv()
        print(output)
    elif args.command == "import-jobs":
        if args.path is None:
            raise SystemExit("--path is required for import-jobs")
        import_jobs(args.path)
    elif args.command == "security-scan":
        security_scan()
    elif args.command == "backup-db":
        output = backup_db()
        print(output)
    elif args.command == "api-smoke":
        api_smoke()
    elif args.command == "dashboard-smoke":
        dashboard_smoke()
    elif args.command == "docker-check":
        docker_check()


if __name__ == "__main__":
    main()
