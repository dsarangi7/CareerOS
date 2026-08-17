import streamlit as st
from sqlalchemy import select

from app.db.base import SessionLocal
from app.models.entities import Communication

st.set_page_config(page_title="Communications", layout="wide")
st.title("Communications")

with SessionLocal() as session:
    st.dataframe(
        list(session.scalars(select(Communication))), use_container_width=True, hide_index=True
    )
