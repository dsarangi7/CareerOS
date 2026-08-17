from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.main import app
from app.db.base import Base, get_session
from app.models import entities  # noqa: F401


def test_agent_api_lists_definitions_and_runs_mock_agent() -> None:
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
        definitions = client.get("/agents/definitions")
        assert definitions.status_code == 200
        assert len(definitions.json()) == 12

        result = client.post(
            "/agents/run",
            json={
                "agent_name": "job_extraction",
                "subject_type": "JobOpportunity",
                "payload": {"source_text": "Required Python and battery diagnostics."},
            },
        )
        assert result.status_code == 200
        assert result.json()["status"] == "succeeded"
    finally:
        app.dependency_overrides.clear()
