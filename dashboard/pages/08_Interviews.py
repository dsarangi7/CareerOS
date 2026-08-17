import streamlit as st
from sqlalchemy import select

from app.db.base import SessionLocal
from app.models.entities import Interview, InterviewPreparationPack

st.set_page_config(page_title="Interviews", layout="wide")
st.title("Interviews")

with SessionLocal() as session:
    st.subheader("Interview Records")
    st.dataframe(
        list(session.scalars(select(Interview))), use_container_width=True, hide_index=True
    )
    st.subheader("Preparation Packs")
    st.dataframe(
        list(session.scalars(select(InterviewPreparationPack))),
        use_container_width=True,
        hide_index=True,
    )
