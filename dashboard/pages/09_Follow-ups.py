import streamlit as st
from sqlalchemy import select

from app.db.base import SessionLocal
from app.models.entities import FollowUp

st.set_page_config(page_title="Follow-ups", layout="wide")
st.title("Follow-ups")

with SessionLocal() as session:
    st.dataframe(list(session.scalars(select(FollowUp))), use_container_width=True, hide_index=True)
