import streamlit as st
from sqlalchemy import select

from app.db.base import SessionLocal
from app.models.entities import CVBaseVersion, TailoredCV

st.set_page_config(page_title="CV Library", layout="wide")
st.title("CV Library")

with SessionLocal() as session:
    st.subheader("Base CVs")
    st.dataframe(
        list(session.scalars(select(CVBaseVersion))), use_container_width=True, hide_index=True
    )
    st.subheader("Tailored CVs")
    st.dataframe(
        list(session.scalars(select(TailoredCV))), use_container_width=True, hide_index=True
    )
