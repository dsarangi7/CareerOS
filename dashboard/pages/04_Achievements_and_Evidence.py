import streamlit as st
from sqlalchemy import select

from app.db.base import SessionLocal
from app.models.entities import Achievement, EvidenceRecord
from app.schemas.evidence import AchievementCreate, EvidenceRecordCreate
from app.services.evidence import create_achievement, create_evidence

st.set_page_config(page_title="Achievements and Evidence", layout="wide")
st.title("Achievements and Evidence")

with SessionLocal() as session:
    st.subheader("Achievement Bank")
    st.dataframe(
        list(session.scalars(select(Achievement))), use_container_width=True, hide_index=True
    )
    profile_id = st.text_input("Profile ID")
    with st.expander("Add achievement"):
        title = st.text_input("Achievement title")
        description = st.text_area("Achievement description")
        if st.button("Add achievement", disabled=not profile_id or not title):
            create_achievement(
                session,
                profile_id,
                AchievementCreate(title=title, description=description),
            )
            session.commit()
            st.rerun()
    st.subheader("Evidence Records")
    st.dataframe(
        list(session.scalars(select(EvidenceRecord))), use_container_width=True, hide_index=True
    )
    with st.expander("Add evidence"):
        achievement_id = st.text_input("Achievement ID")
        evidence_title = st.text_input("Evidence title")
        source_type = st.text_input("Source type", value="note")
        source_ref = st.text_area("Source reference")
        if st.button("Add evidence", disabled=not evidence_title or not source_type):
            create_evidence(
                session,
                EvidenceRecordCreate(
                    achievement_id=achievement_id or None,
                    title=evidence_title,
                    source_type=source_type,
                    source_ref=source_ref,
                ),
            )
            session.commit()
            st.rerun()
