from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.main import app
from app.db.base import Base, get_session
from app.models import entities  # noqa: F401
from app.services.profile import seed_candidate_profile


def test_profile_skill_achievement_evidence_crud_api() -> None:
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
        with factory() as seed_session:
            profile = seed_candidate_profile(seed_session)
            seed_session.commit()
            profile_id = profile.id

        client = TestClient(app)
        skill_response = client.post(
            f"/profiles/{profile_id}/skills",
            json={"name": "Pytest evidence CRUD", "category": "test"},
        )
        assert skill_response.status_code == 201
        assert skill_response.json()["verification_status"] == "user_reported_pending_evidence"

        achievement_response = client.post(
            f"/profiles/{profile_id}/achievements",
            json={
                "title": "Built a tested evidence workflow",
                "description": "Synthetic integration-test achievement.",
            },
        )
        assert achievement_response.status_code == 201
        achievement_id = achievement_response.json()["id"]

        evidence_response = client.post(
            "/evidence",
            json={
                "achievement_id": achievement_id,
                "title": "Integration test evidence",
                "source_type": "test_fixture",
                "source_ref": "tests/integration/test_profile_evidence_api.py",
            },
        )
        assert evidence_response.status_code == 201
        assert evidence_response.json()["verification_status"] == "requires_confirmation"

        list_response = client.get(f"/profiles/{profile_id}/achievements")
        assert list_response.status_code == 200
        assert any(item["id"] == achievement_id for item in list_response.json())

        verification_response = client.patch(
            f"/records/achievements/{achievement_id}/verification",
            json={"verification_status": "verified"},
        )
        assert verification_response.status_code == 200
        assert verification_response.json()["verification_status"] == "verified"

        queue_response = client.get(f"/profiles/{profile_id}/review-queue")
        assert queue_response.status_code == 200
        assert "skills" in queue_response.json()

        delete_response = client.delete(f"/records/achievements/{achievement_id}")
        assert delete_response.status_code == 204
    finally:
        app.dependency_overrides.clear()
