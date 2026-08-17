from collections import Counter

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import select

from app.db.base import SessionLocal, create_all
from app.models.entities import JobOpportunity

st.set_page_config(page_title="CareerOS", layout="wide")
create_all()

st.title("CareerOS")
st.caption("Local career intelligence dashboard")

with SessionLocal() as session:
    jobs = list(session.scalars(select(JobOpportunity)))

status_counts = Counter(str(job.status) for job in jobs)
cols = st.columns(4)
cols[0].metric("New opportunities", status_counts.get("discovered", 0))
cols[1].metric("Priority opportunities", 0)
cols[2].metric("Awaiting review", status_counts.get("awaiting_review", 0))
cols[3].metric("Submitted applications", status_counts.get("applied", 0))

data = pd.DataFrame(
    [
        {"title": job.title, "country": job.country or "Unknown", "status": str(job.status)}
        for job in jobs
    ]
)
if data.empty:
    st.info("Run `python -m scripts.tasks seed` to load the starter profile and demo jobs.")
else:
    left, right = st.columns(2)
    with left:
        st.subheader("Applications by Country")
        st.plotly_chart(px.histogram(data, x="country"), use_container_width=True)
    with right:
        st.subheader("Pipeline")
        st.dataframe(data, use_container_width=True, hide_index=True)
