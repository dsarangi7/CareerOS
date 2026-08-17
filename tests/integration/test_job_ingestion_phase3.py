from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.main import app
from app.core.enums import JobStatus, SponsorshipStatus
from app.db.base import Base, get_session
from app.models import entities  # noqa: F401
from app.models.entities import JobOpportunity
from app.services.jobs import ingest_job_description

JOB_TEXT = """
Company: Volt Marine Analytics
Title: Battery Diagnostics Engineer
Location: Rotterdam
Country: Netherlands

Required: Python experience for battery diagnostics and anomaly detection.
Required skill: BMS, SOC, SOH analysis.
Visa sponsorship may sponsor exceptional candidates.
"""


def test_ingest_job_description_extracts_requirements_scores_and_sponsorship(session) -> None:  # type: ignore[no-untyped-def]
    job, duplicate_of, requirements, sponsorship, fit = ingest_job_description(
        session,
        source_text=JOB_TEXT,
        source_url="https://example.test/jobs/battery-diagnostics",
    )
    session.commit()

    assert duplicate_of is None
    assert job.status == JobStatus.ASSESSED
    assert job.title == "Battery Diagnostics Engineer"
    assert len(requirements) >= 2
    assert sponsorship.classification == SponsorshipStatus.POSSIBLY_AVAILABLE
    assert fit.total_score > 0

    second_job, duplicate_id, *_ = ingest_job_description(
        session,
        source_text=JOB_TEXT,
        source_url="https://example.test/jobs/battery-diagnostics-copy",
    )
    session.commit()

    assert second_job.id != job.id
    assert duplicate_id == job.id


def test_ingest_job_api_returns_structured_result() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_session() -> Generator[Session, None, None]:
        with factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        client = TestClient(app)
        response = client.post(
            "/opportunities/ingest",
            json={
                "source_text": JOB_TEXT,
                "source_url": "https://example.test/jobs/api-ingest",
            },
        )
        assert response.status_code == 201
        payload = response.json()
        job_id = payload["job"]["id"]
        assert payload["requirements"]
        assert payload["sponsorship"]["classification"] == "possibly_available"
        assert payload["fit_assessment"]["total_score"] > 0

        requirements_response = client.get(f"/opportunities/{job_id}/requirements")
        assert requirements_response.status_code == 200
        assert requirements_response.json()

        with factory() as session:
            stored_job = session.scalar(select(JobOpportunity).where(JobOpportunity.id == job_id))
            assert stored_job is not None
    finally:
        app.dependency_overrides.clear()
