import streamlit as st
from sqlalchemy import select

from app.db.base import SessionLocal
from app.models.entities import (
    Company,
    JobFitAssessment,
    JobOpportunity,
    JobRequirement,
    SponsorshipAssessment,
)

st.set_page_config(page_title="Opportunity Detail", layout="wide")
st.title("Opportunity Detail")

with SessionLocal() as session:
    rows = session.execute(select(JobOpportunity, Company).join(Company, isouter=True)).all()
    options = {
        f"{company.name if company else 'Unknown'} - {job.title}": job.id for job, company in rows
    }
    if not options:
        st.info("No opportunities available.")
        st.stop()
    selected = st.selectbox("Opportunity", list(options))
    job = session.get(JobOpportunity, options[selected])
    if job is None:
        st.stop()
    requirements = list(
        session.scalars(select(JobRequirement).where(JobRequirement.job_id == job.id))
    )
    fit = session.scalar(
        select(JobFitAssessment)
        .where(JobFitAssessment.job_id == job.id)
        .order_by(JobFitAssessment.created_at.desc())
    )
    sponsorship = session.scalar(
        select(SponsorshipAssessment)
        .where(SponsorshipAssessment.job_id == job.id)
        .order_by(SponsorshipAssessment.created_at.desc())
    )

cols = st.columns(4)
cols[0].metric("Status", str(job.status))
cols[1].metric("Country", job.country or "Unknown")
cols[2].metric("Fit score", f"{fit.total_score:.1f}" if fit else "Not scored")
cols[3].metric("Sponsorship", str(sponsorship.classification) if sponsorship else "Unknown")

st.subheader("Requirements")
st.dataframe(
    [
        {"category": item.category, "required": item.required, "text": item.text}
        for item in requirements
    ],
    use_container_width=True,
    hide_index=True,
)

st.subheader("Source Text")
st.text_area("Stored source", job.source_text, height=280, disabled=True)
