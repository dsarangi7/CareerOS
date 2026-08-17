from fastapi.testclient import TestClient

from app.api.main import app
from app.db.base import Base, make_engine
from app.services.profile import seed_candidate_profile


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_seed_candidate_profile(session) -> None:  # type: ignore[no-untyped-def]
    profile = seed_candidate_profile(session)
    session.commit()

    assert profile.name == "Dibya Jyoti Sarangi"
    assert profile.review_notes


def test_database_metadata_creates_all_tables() -> None:
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    table_names = set(Base.metadata.tables)

    assert "candidate_profiles" in table_names
    assert "job_opportunities" in table_names
    assert "human_approvals" in table_names
