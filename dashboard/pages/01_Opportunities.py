import streamlit as st
from sqlalchemy import select

from app.db.base import SessionLocal
from app.models.entities import Company, JobOpportunity

st.set_page_config(page_title="Opportunities", layout="wide")
st.title("Opportunities")

with SessionLocal() as session:
    rows = session.execute(select(JobOpportunity, Company).join(Company, isouter=True)).all()

st.dataframe(
    [
        {
            "company": company.name if company else "",
            "title": job.title,
            "location": job.location,
            "country": job.country,
            "status": str(job.status),
            "source_url": job.source_url,
        }
        for job, company in rows
    ],
    use_container_width=True,
    hide_index=True,
)
