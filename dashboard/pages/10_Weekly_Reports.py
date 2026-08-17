import streamlit as st
from sqlalchemy import select

from app.db.base import SessionLocal
from app.models.entities import WeeklyReport

st.set_page_config(page_title="Weekly Reports", layout="wide")
st.title("Weekly Reports")

with SessionLocal() as session:
    st.dataframe(
        list(session.scalars(select(WeeklyReport))), use_container_width=True, hide_index=True
    )
