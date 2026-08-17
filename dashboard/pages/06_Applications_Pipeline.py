import streamlit as st
from sqlalchemy import select

from app.db.base import SessionLocal
from app.models.entities import Application, JobOpportunity

st.set_page_config(page_title="Applications Pipeline", layout="wide")
st.title("Applications Pipeline")

with SessionLocal() as session:
    st.dataframe(
        list(session.scalars(select(Application))), use_container_width=True, hide_index=True
    )
    st.subheader("Job Status Register")
    st.dataframe(
        list(session.scalars(select(JobOpportunity))), use_container_width=True, hide_index=True
    )
