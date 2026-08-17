import streamlit as st
from sqlalchemy import select

from app.db.base import SessionLocal
from app.models.entities import (
    Achievement,
    CandidateProfile,
    EducationRecord,
    EmploymentRecord,
    Skill,
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
        st.subheader("Education")
        st.dataframe(list(session.scalars(select(EducationRecord))), hide_index=True)
        st.subheader("Skills and Themes")
        st.dataframe(list(session.scalars(select(Skill))), hide_index=True)
        st.subheader("Achievements")
        st.dataframe(list(session.scalars(select(Achievement))), hide_index=True)
