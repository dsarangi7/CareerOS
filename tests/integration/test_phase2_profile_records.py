from pathlib import Path

from app.core.enums import VerificationStatus
from app.models.entities import Skill
from app.schemas.evidence import (
    EducationRecordCreate,
    EmploymentRecordCreate,
    ProjectCreate,
    SkillCreate,
)
from app.services.evidence import (
    create_education_record,
    create_employment_record,
    create_project,
    create_skill,
    get_review_queue,
    list_skills,
    soft_delete_record,
    update_verification_status,
)
from app.services.profile import seed_candidate_profile
from app.services.profile_io import export_profile_workbook


def test_phase2_profile_records_review_queue_and_export(session, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    profile = seed_candidate_profile(session)
    employment = create_employment_record(
        session,
        profile.id,
        EmploymentRecordCreate(employer="Example Energy", title="R&D Engineer"),
    )
    education = create_education_record(
        session,
        profile.id,
        EducationRecordCreate(institution="Example Institute", degree="M.Tech"),
    )
    skill = create_skill(session, profile.id, SkillCreate(name="Phase 2 unique skill"))
    project = create_project(session, profile.id, ProjectCreate(name="Evidence workflow"))
    session.flush()

    update_verification_status(session, skill.__class__, skill.id, VerificationStatus.VERIFIED)
    soft_delete_record(session, Skill, skill.id)
    queue = get_review_queue(session, profile.id)
    export_path = export_profile_workbook(session, profile.id, tmp_path / "profile.xlsx")

    assert employment.id
    assert education.id
    assert project.id
    assert skill not in list_skills(session, profile.id)
    assert queue["employment"]
    assert queue["education"]
    assert queue["projects"]
    assert export_path.exists()
