from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import SponsorshipStatus
from app.models.entities import (
    WatchCompany,
    WatchJob,
    WatchJobAssessment,
    WatchJobSource,
    WatchScanRun,
)

ROOT = Path(__file__).resolve().parents[2]
SEED_PATH = ROOT / "data" / "watchlist" / "battery_company_watchlist.json"

KEYWORD_FAMILIES: dict[str, list[str]] = {
    "battery_analytics": [
        "battery analytics",
        "battery data",
        "battery diagnostics",
        "battery intelligence",
        "field data",
        "fleet data",
        "operational data",
        "time-series",
        "predictive maintenance",
        "anomaly detection",
        "failure analysis",
        "state of health",
        "soh",
        "remaining useful life",
        "rul",
        "degradation",
        "ageing",
        "lifetime prediction",
    ],
    "bms_algorithms": [
        "battery management system",
        "bms",
        "bms algorithm",
        "soc",
        "state of charge",
        "state estimation",
        "ekf",
        "ukf",
        "kalman filter",
        "equivalent circuit model",
        "ecm",
        "parameter estimation",
        "cell balancing",
        "thermal management",
        "battery controls",
        "embedded algorithm",
    ],
    "ai_software": [
        "machine learning",
        "applied ai",
        "industrial ai",
        "data scientist",
        "data engineer",
        "ml engineer",
        "scientific software",
        "python",
        "matlab",
        "simulink",
        "digital twin",
        "rag",
        "knowledge systems",
        "engineering automation",
        "engineering tools",
        "software engineer",
    ],
    "energy_marine": [
        "marine battery",
        "vessel electrification",
        "hybrid propulsion",
        "electric vessel",
        "energy management system",
        "ems",
        "bess",
        "energy storage",
        "power management",
        "inverter control",
        "load profile",
        "fast charging",
        "high c-rate",
    ],
}

NEGATIVE_FILTERS = [
    "electrode synthesis",
    "electrolyte formulation",
    "materials discovery",
    "production operator",
    "maintenance technician",
    "pure mechanical cad",
    "security clearance",
    "citizenship required",
    "native language",
    "no sponsorship",
    "unable to sponsor",
    "will not sponsor",
]

HARD_RESTRICTION_PHRASES = {
    "citizenship_required": ["citizenship required", "must be a citizen", "citizen required"],
    "security_clearance_required": ["security clearance", "active clearance", "security cleared"],
    "no_sponsorship": ["no sponsorship", "unable to sponsor", "will not sponsor"],
}

ATS_PATTERNS: list[tuple[str, str]] = [
    ("Greenhouse", "greenhouse.io"),
    ("Lever", "lever.co"),
    ("Ashby", "ashbyhq.com"),
    ("Workday", "myworkdayjobs.com"),
    ("SmartRecruiters", "smartrecruiters.com"),
    ("SuccessFactors", "successfactors"),
    ("Taleo", "taleo.net"),
    ("iCIMS", "icims.com"),
    ("Recruitee", "recruitee.com"),
    ("Teamtailor", "teamtailor.com"),
]


class ScanStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    MANUAL_REVIEW = "manual_review"


@dataclass(frozen=True)
class NormalizedJob:
    company_name: str
    title: str
    original_url: str
    application_url: str
    source: str
    external_job_id: str | None = None
    location: str | None = None
    country: str | None = None
    work_mode: str | None = None
    publication_date: str | None = None
    full_description: str = ""
    department: str | None = None
    seniority: str | None = None
    salary: str | None = None
    required_skills: tuple[str, ...] = ()
    preferred_skills: tuple[str, ...] = ()
    experience_requirement: str | None = None
    education_requirement: str | None = None
    language_requirement: str | None = None
    visa_wording: str | None = None
    citizenship_restriction: str | None = None
    security_clearance_restriction: str | None = None
    closing_date: str | None = None
    active: bool = True

    @property
    def content_hash(self) -> str:
        payload = "\n".join(
            [
                self.company_name,
                self.title,
                self.location or "",
                self.full_description,
                self.application_url,
            ]
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def seed_watchlist_companies(session: Session, seed_path: Path = SEED_PATH) -> int:
    data = json.loads(seed_path.read_text(encoding="utf-8"))
    upserted = 0
    for row in data["companies"]:
        company = session.scalar(
            select(WatchCompany).where(WatchCompany.canonical_name == row["canonical_name"])
        )
        if company is None:
            company = WatchCompany(canonical_name=row["canonical_name"])
            session.add(company)
        for key, value in row.items():
            setattr(company, key, value)
        upserted += 1
    session.flush()
    return upserted


def tier_schedule_days(tier: str) -> list[int]:
    if tier == "A":
        return [0, 1, 2, 3, 4, 5, 6]
    if tier == "B":
        return [0, 2, 4]
    if tier == "C":
        return [0]
    raise ValueError(f"Unknown watchlist tier: {tier}")


def should_scan_tier(tier: str, now: datetime | None = None) -> bool:
    current = now or datetime.now(UTC)
    return current.weekday() in tier_schedule_days(tier)


def detect_ats(url: str | None, html: str = "") -> str:
    haystack = f"{url or ''}\n{html}".lower()
    for name, marker in ATS_PATTERNS:
        if marker.lower() in haystack:
            return name
    if "api" in haystack and ("jobs" in haystack or "careers" in haystack):
        return "Company-specific JSON/API"
    if html.strip():
        return "Static HTML"
    return "Unknown"


def normalize_job(raw: dict[str, Any], company_name: str, source: str) -> NormalizedJob:
    title = clean_text(str(raw.get("title") or raw.get("name") or "Untitled Role"))[:250]
    url = str(raw.get("application_url") or raw.get("url") or "").strip()
    description = sanitize_job_text(str(raw.get("description") or raw.get("content") or ""))
    location = clean_text(str(raw.get("location") or raw.get("city") or "")) or None
    country = clean_text(str(raw.get("country") or "")) or infer_country(location)
    return NormalizedJob(
        company_name=company_name,
        title=title,
        original_url=str(raw.get("original_url") or url),
        application_url=url,
        source=source,
        external_job_id=clean_text(str(raw.get("id") or raw.get("external_job_id") or "")) or None,
        location=location,
        country=country,
        work_mode=clean_text(str(raw.get("work_mode") or ""))
        or infer_work_mode(description + " " + (location or "")),
        publication_date=clean_text(
            str(raw.get("publication_date") or raw.get("published_at") or "")
        )
        or None,
        full_description=description,
        department=clean_text(str(raw.get("department") or "")) or None,
        seniority=clean_text(str(raw.get("seniority") or "")) or infer_seniority(title),
        salary=clean_text(str(raw.get("salary") or "")) or None,
        required_skills=tuple(extract_required_skills(description)),
        preferred_skills=tuple(extract_preferred_skills(description)),
        experience_requirement=extract_line(description, ["experience"]),
        education_requirement=extract_line(description, ["degree", "education", "phd", "master"]),
        language_requirement=extract_line(
            description, ["language", "english", "german", "chinese"]
        ),
        visa_wording=extract_line(
            description, ["visa", "sponsor", "work authorization", "right to work"]
        ),
        citizenship_restriction=extract_line(description, ["citizen", "citizenship"]),
        security_clearance_restriction=extract_line(description, ["clearance"]),
        closing_date=clean_text(str(raw.get("closing_date") or "")) or None,
        active=bool(raw.get("active", True)),
    )


def dedupe_key(job: NormalizedJob) -> str:
    if job.application_url:
        return f"url:{canonicalize_url(job.application_url)}"
    if job.external_job_id:
        return f"external:{job.company_name.lower()}:{job.external_job_id}"
    compact = "|".join([job.company_name.lower(), job.title.lower(), (job.location or "").lower()])
    return "role:" + hashlib.sha256(compact.encode("utf-8")).hexdigest()


def upsert_watch_job(
    session: Session, company: WatchCompany, normalized: NormalizedJob
) -> tuple[WatchJob, bool, bool]:
    key = dedupe_key(normalized)
    existing = session.scalar(select(WatchJob).where(WatchJob.dedupe_key == key))
    is_new = existing is None
    changed = False
    job = existing or WatchJob(company_id=company.id, dedupe_key=key)
    previous_hash = job.content_hash
    job.company_id = company.id
    job.title = normalized.title
    job.original_url = normalized.original_url
    job.application_url = normalized.application_url
    job.source = normalized.source
    job.external_job_id = normalized.external_job_id
    job.location = normalized.location
    job.country = normalized.country
    job.work_mode = normalized.work_mode
    job.publication_date = normalized.publication_date
    job.retrieval_date = datetime.now(UTC)
    job.full_description = normalized.full_description
    job.department = normalized.department
    job.seniority = normalized.seniority
    job.salary = normalized.salary
    job.required_skills = list(normalized.required_skills)
    job.preferred_skills = list(normalized.preferred_skills)
    job.experience_requirement = normalized.experience_requirement
    job.education_requirement = normalized.education_requirement
    job.language_requirement = normalized.language_requirement
    job.visa_wording = normalized.visa_wording
    job.citizenship_restriction = normalized.citizenship_restriction
    job.security_clearance_restriction = normalized.security_clearance_restriction
    job.closing_date = normalized.closing_date
    job.content_hash = normalized.content_hash
    job.active_status = "active" if normalized.active else "expired"
    history = list(job.scan_history or [])
    history.append({"at": datetime.now(UTC).isoformat(), "hash": normalized.content_hash})
    job.scan_history = history[-20:]
    if existing is None:
        session.add(job)
    elif previous_hash and previous_hash != normalized.content_hash:
        changed = True
    session.flush()
    return job, is_new, changed


def mark_expired_missing_jobs(session: Session, company: WatchCompany, seen_keys: set[str]) -> int:
    expired = 0
    jobs = session.scalars(
        select(WatchJob).where(
            WatchJob.company_id == company.id, WatchJob.active_status == "active"
        )
    )
    for job in jobs:
        if job.dedupe_key not in seen_keys:
            job.active_status = "expired"
            expired += 1
    session.flush()
    return expired


def assess_job(job: WatchJob) -> dict[str, Any]:
    text = " ".join(
        [job.title or "", job.full_description or "", " ".join(job.required_skills or [])]
    )
    lowered = text.lower()
    matches = {
        family: [kw for kw in kws if kw.lower() in lowered]
        for family, kws in KEYWORD_FAMILIES.items()
    }
    matched_terms = sorted({kw for kws in matches.values() for kw in kws})
    negative = [term for term in NEGATIVE_FILTERS if term in lowered]
    hard = hard_restrictions(text)
    sponsorship = classify_sponsorship_text(text)
    technical = min(45, len(matched_terms) * 4)
    transferable = (
        15
        if any(k in lowered for k in ["python", "matlab", "data", "software", "engineering"])
        else 6
    )
    eligibility = (
        0 if hard else (15 if sponsorship != SponsorshipStatus.EXPLICITLY_UNAVAILABLE else 0)
    )
    domain = (
        20
        if any(matches[f] for f in ["battery_analytics", "bms_algorithms", "energy_marine"])
        else 8
    )
    penalty = min(20, len(negative) * 5)
    fit = max(0, min(100, technical + transferable + eligibility + domain - penalty))
    if hard:
        fit = min(fit, 45)
    action = action_for_score(fit, hard)
    return {
        "fit_score": fit,
        "eligibility_score": eligibility,
        "sponsorship_status": sponsorship.value,
        "technical_match": matched_terms,
        "transferable_match": ["engineering analytics"] if transferable >= 15 else [],
        "missing_requirements": negative,
        "hard_restrictions": hard,
        "recommended_cv_lane": cv_lane(matches),
        "recommended_action": action,
        "confidence": 0.72 if text.strip() else 0.2,
        "evidence_mapping": {
            term: "approved master-profile evidence required" for term in matched_terms[:12]
        },
        "application_urgency": urgency_for_score(fit, hard),
    }


def store_watch_assessment(session: Session, job: WatchJob) -> WatchJobAssessment:
    result = assess_job(job)
    existing = session.scalar(
        select(WatchJobAssessment).where(WatchJobAssessment.watch_job_id == job.id)
    )
    assessment = existing or WatchJobAssessment(watch_job_id=job.id)
    for key, value in result.items():
        setattr(assessment, key, value)
    if existing is None:
        session.add(assessment)
    session.flush()
    return assessment


def run_watch_scan(
    session: Session,
    *,
    tier: str | None = None,
    company_limit: int | None = None,
    live: bool = False,
) -> dict[str, Any]:
    query = select(WatchCompany).order_by(WatchCompany.priority_tier, WatchCompany.canonical_name)
    if tier:
        query = query.where(WatchCompany.priority_tier == tier)
    companies = list(session.scalars(query))
    if company_limit is not None:
        companies = companies[:company_limit]
    run = WatchScanRun(
        tier=tier or "manual",
        scan_type="live" if live else "offline",
        status=ScanStatus.PENDING.value,
        started_at=datetime.now(UTC),
    )
    session.add(run)
    session.flush()
    summary: dict[str, Any] = {
        "companies": 0,
        "new_jobs": 0,
        "changed_jobs": 0,
        "expired_jobs": 0,
        "failures": [],
    }
    for company in companies:
        company.scan_status = ScanStatus.PENDING.value
        html = ""
        detected = company.ats_type or company.careers_platform or "Unknown"
        jobs: list[NormalizedJob] = []
        try:
            if live and company.official_careers_url:
                html = fetch_public_page(company.official_careers_url)
                detected = detect_ats(company.official_careers_url, html)
                jobs = extract_jobs_from_html(company, html)
            source = WatchJobSource(
                company_id=company.id,
                source_url=company.official_careers_url,
                source_type="official_careers_html" if live else "seed_metadata",
                ats_detected=detected,
                status=ScanStatus.SUCCEEDED.value
                if (html or not live)
                else ScanStatus.MANUAL_REVIEW.value,
                http_status=200 if html else None,
                checked_at=datetime.now(UTC),
            )
            session.add(source)
            company.ats_type = detected
            company.last_careers_page_verification = datetime.now(UTC)
            company.last_successful_scan = (
                datetime.now(UTC)
                if source.status == ScanStatus.SUCCEEDED.value
                else company.last_successful_scan
            )
            company.scan_status = source.status
            seen: set[str] = set()
            for normalized in jobs:
                normalized_key = dedupe_key(normalized)
                if normalized_key in seen:
                    continue
                watch_job, is_new, changed = upsert_watch_job(session, company, normalized)
                store_watch_assessment(session, watch_job)
                seen.add(watch_job.dedupe_key)
                summary["new_jobs"] += int(is_new)
                summary["changed_jobs"] += int(changed)
            expired = mark_expired_missing_jobs(session, company, seen) if live and jobs else 0
            company.active_job_count = count_company_jobs(session, company, active=True)
            company.relevant_job_count = count_relevant_jobs(session, company)
            summary["expired_jobs"] += expired
            summary["companies"] += 1
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            company.scan_status = ScanStatus.MANUAL_REVIEW.value
            company.manual_review_status = "required"
            summary["failures"].append({"company": company.canonical_name, "error": str(exc)[:300]})
    run.finished_at = datetime.now(UTC)
    run.status = (
        ScanStatus.SUCCEEDED.value if not summary["failures"] else ScanStatus.MANUAL_REVIEW.value
    )
    run.summary = summary
    session.flush()
    return summary | {"scan_run_id": run.id}


def fetch_public_page(url: str, timeout: int = 15) -> str:
    request = Request(
        url, headers={"User-Agent": "CareerOS local validation bot; official careers page check"}
    )
    with urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("content-type", "")
        if "text" not in content_type and "html" not in content_type and "json" not in content_type:
            raise ValueError(f"Unsupported content type: {content_type}")
        body = response.read(1_000_000)
        if not isinstance(body, bytes):
            body = bytes(body)
        return body.decode("utf-8", errors="replace")


def extract_jobs_from_html(company: WatchCompany, html: str) -> list[NormalizedJob]:
    text = sanitize_job_text(strip_html(html))
    jobs: list[NormalizedJob] = []
    for line in text.splitlines():
        cleaned = clean_text(line)
        if is_probable_relevant_title(cleaned):
            jobs.append(
                normalize_job(
                    {"title": cleaned, "description": cleaned, "url": company.official_careers_url},
                    company.canonical_name,
                    "official_careers_html",
                )
            )
    return jobs[:50]


def classify_sponsorship_text(source_text: str) -> SponsorshipStatus:
    text = source_text.lower()
    if any(p in text for p in ["security clearance", "active clearance"]):
        return SponsorshipStatus.SECURITY_CLEARANCE_REQUIRED
    if any(p in text for p in ["citizenship required", "must be a citizen", "citizen required"]):
        return SponsorshipStatus.CITIZENSHIP_REQUIRED
    if any(p in text for p in ["no sponsorship", "unable to sponsor", "will not sponsor"]):
        return SponsorshipStatus.EXPLICITLY_UNAVAILABLE
    if any(p in text for p in ["must already be authorized", "right to work"]):
        return SponsorshipStatus.REQUIRES_EXISTING_WORK_AUTHORIZATION
    if any(p in text for p in ["visa sponsorship available", "will sponsor"]):
        return SponsorshipStatus.EXPLICITLY_AVAILABLE
    if any(p in text for p in ["may sponsor", "sponsorship considered"]):
        return SponsorshipStatus.POSSIBLY_AVAILABLE
    return SponsorshipStatus.NOT_MENTIONED


def hard_restrictions(text: str) -> list[str]:
    lowered = text.lower()
    return [
        name
        for name, phrases in HARD_RESTRICTION_PHRASES.items()
        if any(p in lowered for p in phrases)
    ]


def action_for_score(score: float, hard: list[str]) -> str:
    if hard:
        return "ineligible_or_visa_blocked"
    if score >= 90:
        return "immediate_priority_alert"
    if score >= 80:
        return "high_priority_shortlist"
    if score >= 70:
        return "weekly_review"
    if score >= 60:
        return "archive_unless_strategic"
    return "archive_without_notification"


def urgency_for_score(score: float, hard: list[str]) -> str:
    if hard:
        return "blocked"
    if score >= 90:
        return "immediate"
    if score >= 80:
        return "high"
    if score >= 70:
        return "weekly"
    return "low"


def cv_lane(matches: dict[str, list[str]]) -> str:
    if matches["bms_algorithms"]:
        return "battery_modelling_bms"
    if matches["battery_analytics"] or matches["energy_marine"]:
        return "battery_diagnostics_analytics"
    if matches["ai_software"]:
        return "industrial_ai_software"
    return "general_engineering"


def count_company_jobs(session: Session, company: WatchCompany, *, active: bool) -> int:
    query = select(func.count()).select_from(WatchJob).where(WatchJob.company_id == company.id)
    if active:
        query = query.where(WatchJob.active_status == "active")
    return int(session.scalar(query) or 0)


def count_relevant_jobs(session: Session, company: WatchCompany) -> int:
    return int(
        session.scalar(
            select(func.count())
            .select_from(WatchJob)
            .join(WatchJobAssessment)
            .where(
                WatchJob.company_id == company.id,
                WatchJob.active_status == "active",
                WatchJobAssessment.fit_score >= 70,
            )
        )
        or 0
    )


def extract_required_skills(text: str) -> list[str]:
    lowered = text.lower()
    return sorted({kw for kws in KEYWORD_FAMILIES.values() for kw in kws if kw.lower() in lowered})


def extract_preferred_skills(text: str) -> list[str]:
    return extract_required_skills(text)


def extract_line(text: str, terms: list[str]) -> str | None:
    for line in text.splitlines():
        lowered = line.lower()
        if any(term in lowered for term in terms):
            return clean_text(line)[:500]
    return None


def clean_text(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value.replace("\x00", " ")).strip()
    return cleaned


def sanitize_job_text(value: str) -> str:
    suspicious = [
        "ignore previous instructions",
        "system prompt",
        "developer message",
        "exfiltrate",
    ]
    cleaned_lines = []
    for line in value.splitlines():
        lowered = line.lower()
        if any(marker in lowered for marker in suspicious):
            cleaned_lines.append("[removed prompt-injection-like text]")
        else:
            cleaned_lines.append(line[:2000])
    return "\n".join(cleaned_lines)[:50000]


def strip_html(html: str) -> str:
    html = re.sub(r"(?is)<(script|style).*?>.*?</\1>", "\n", html)
    html = re.sub(r"(?s)<[^>]+>", "\n", html)
    html = re.sub(r"&nbsp;", " ", html)
    html = re.sub(r"&amp;", "&", html)
    return html


def is_probable_relevant_title(text: str) -> bool:
    if not (8 <= len(text) <= 160):
        return False
    lowered = text.lower()
    title_terms = [
        "battery",
        "bms",
        "energy storage",
        "data",
        "software",
        "algorithm",
        "diagnostic",
        "ai",
        "machine learning",
        "marine",
    ]
    return any(term in lowered for term in title_terms) and not lowered.startswith(
        ("privacy", "cookie", "sign in")
    )


def infer_country(location: str | None) -> str | None:
    if not location:
        return None
    known = [
        "China",
        "Germany",
        "United States",
        "France",
        "Finland",
        "Sweden",
        "Norway",
        "Netherlands",
        "United Kingdom",
        "India",
        "Japan",
        "Korea",
        "Singapore",
    ]
    for country in known:
        if country.lower() in location.lower():
            return country
    return None


def infer_work_mode(text: str) -> str | None:
    lowered = text.lower()
    if "remote" in lowered:
        return "remote"
    if "hybrid" in lowered:
        return "hybrid"
    if "onsite" in lowered or "on-site" in lowered:
        return "onsite"
    return None


def infer_seniority(title: str) -> str | None:
    lowered = title.lower()
    if "senior" in lowered or "lead" in lowered or "principal" in lowered:
        return "senior"
    if "manager" in lowered or "director" in lowered:
        return "leadership"
    if "intern" in lowered or "graduate" in lowered:
        return "early_career"
    return None


def canonicalize_url(url: str) -> str:
    return url.strip().rstrip("/").lower()


def next_due_at(tier: str, now: datetime | None = None, hour: int = 7) -> datetime:
    current = now or datetime.now(UTC)
    for offset in range(8):
        candidate = (current + timedelta(days=offset)).replace(
            hour=hour, minute=0, second=0, microsecond=0
        )
        if candidate >= current and candidate.weekday() in tier_schedule_days(tier):
            return candidate
    raise RuntimeError("Could not compute next due time")
