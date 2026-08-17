import streamlit as st
from sqlalchemy import select

from app.db.base import SessionLocal
from app.models.entities import Achievement, EvidenceRecord

st.set_page_config(page_title="Achievements and Evidence", layout="wide")
st.title("Achievements and Evidence")

with SessionLocal() as session:
    st.subheader("Achievement Bank")
    st.dataframe(
        list(session.scalars(select(Achievement))), use_container_width=True, hide_index=True
    )
    st.subheader("Evidence Records")
    st.dataframe(
        list(session.scalars(select(EvidenceRecord))), use_container_width=True, hide_index=True
    )
