import streamlit as st
from sqlalchemy import select

from app.core.enums import VerificationStatus
from app.db.base import SessionLocal
from app.models.entities import (
    Achievement,
    EducationRecord,
    EmploymentRecord,
    EvidenceRecord,
    Skill,
)
from app.services.evidence import update_verification_status

st.set_page_config(page_title="Review Queue", layout="wide")
st.title("Review Queue")

with SessionLocal() as session:
    sections = {
        "Employment": select(EmploymentRecord).where(
            EmploymentRecord.verification_status != VerificationStatus.VERIFIED
        ),
        "Education": select(EducationRecord).where(
            EducationRecord.verification_status != VerificationStatus.VERIFIED
        ),
        "Skills": select(Skill).where(Skill.verification_status != VerificationStatus.VERIFIED),
        "Achievements": select(Achievement).where(
            Achievement.verification_status != VerificationStatus.VERIFIED
        ),
        "Evidence": select(EvidenceRecord).where(
            EvidenceRecord.verification_status != VerificationStatus.VERIFIED
        ),
    }
    for title, query in sections.items():
        st.subheader(title)
        st.dataframe(list(session.scalars(query)), use_container_width=True, hide_index=True)

    st.subheader("Mark Record Verified")
    record_type = st.selectbox(
        "Record type",
        ["EmploymentRecord", "EducationRecord", "Skill", "Achievement", "EvidenceRecord"],
    )
    record_id = st.text_input("Record ID")
    model_map = {
        "EmploymentRecord": EmploymentRecord,
        "EducationRecord": EducationRecord,
        "Skill": Skill,
        "Achievement": Achievement,
        "EvidenceRecord": EvidenceRecord,
    }
    if st.button("Mark verified", disabled=not record_id):
        update_verification_status(
            session, model_map[record_type], record_id, VerificationStatus.VERIFIED
        )
        session.commit()
        st.rerun()
