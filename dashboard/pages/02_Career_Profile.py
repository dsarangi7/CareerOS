import streamlit as st
from sqlalchemy import select

from app.db.base import SessionLocal
from app.models.entities import (
    Achievement,
    CandidateProfile,
    EducationRecord,
    EmploymentRecord,
    Project,
    Skill,
)
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
)

st.set_page_config(page_title="Career Profile", layout="wide")
st.title("Career Profile")

with SessionLocal() as session:
    profile = session.scalar(select(CandidateProfile).order_by(CandidateProfile.created_at))
    if profile is None:
        st.warning("Seed profile not found.")
    else:
        st.header(profile.name)
        st.write(profile.positioning)
        st.info(profile.review_notes)
        st.subheader("Employment")
        st.dataframe(list(session.scalars(select(EmploymentRecord))), hide_index=True)
        with st.expander("Add employment record"):
            employer = st.text_input("Employer")
            title = st.text_input("Title")
            if st.button("Add employment", disabled=not employer or not title):
                create_employment_record(
                    session, profile.id, EmploymentRecordCreate(employer=employer, title=title)
                )
                session.commit()
                st.rerun()
        st.subheader("Education")
        st.dataframe(list(session.scalars(select(EducationRecord))), hide_index=True)
        with st.expander("Add education record"):
            institution = st.text_input("Institution")
            degree = st.text_input("Degree")
            if st.button("Add education", disabled=not institution or not degree):
                create_education_record(
                    session,
                    profile.id,
                    EducationRecordCreate(institution=institution, degree=degree),
                )
                session.commit()
                st.rerun()
        st.subheader("Skills and Themes")
        st.dataframe(list(session.scalars(select(Skill))), hide_index=True)
        with st.expander("Add skill"):
            skill_name = st.text_input("Skill name")
            if st.button("Add skill", disabled=not skill_name):
                create_skill(session, profile.id, SkillCreate(name=skill_name))
                session.commit()
                st.rerun()
        st.subheader("Projects")
        st.dataframe(list(session.scalars(select(Project))), hide_index=True)
        with st.expander("Add project"):
            project_name = st.text_input("Project name")
            if st.button("Add project", disabled=not project_name):
                create_project(session, profile.id, ProjectCreate(name=project_name))
                session.commit()
                st.rerun()
        st.subheader("Achievements")
        st.dataframe(list(session.scalars(select(Achievement))), hide_index=True)
