from __future__ import annotations

from datetime import UTC, datetime

import streamlit as st
from sqlalchemy import select, update

from app.db.base import SessionLocal
from app.models.entities import WatchCompany, WatchJob, WatchJobAssessment, WatchJobSource
from app.watchlist.services import run_watch_scan, seed_watchlist_companies

st.set_page_config(page_title="Company Watchlist", layout="wide")
st.title("Company Watchlist")

with SessionLocal() as session:
    if st.button("Scan Now", type="primary"):
        if not session.scalars(select(WatchCompany)).first():
            seed_watchlist_companies(session)
        summary = run_watch_scan(session, tier=None, company_limit=5, live=False)
        session.commit()
        st.success(f"Scan recorded for {summary['companies']} companies")

    companies = list(
        session.scalars(
            select(WatchCompany).order_by(WatchCompany.priority_tier, WatchCompany.canonical_name)
        )
    )
    jobs = session.execute(
        select(WatchJob, WatchJobAssessment)
        .join(WatchJobAssessment, WatchJobAssessment.watch_job_id == WatchJob.id, isouter=True)
        .order_by(WatchJob.retrieval_date.desc().nullslast())
    ).all()
    source_rows = session.execute(
        select(WatchJobSource, WatchCompany)
        .join(WatchCompany, WatchCompany.id == WatchJobSource.company_id)
        .order_by(WatchJobSource.created_at.desc())
    ).all()

company_rows = [
    {
        "Company": company.canonical_name,
        "Tier": company.priority_tier,
        "Careers URL": company.official_careers_url,
        "ATS": company.ats_type,
        "Countries": ", ".join(company.countries_of_operation or []),
        "Battery Segment": ", ".join(company.battery_segment or []),
        "Last Scan": company.last_successful_scan,
        "Scan Health": company.scan_status,
        "Total Active Jobs": company.active_job_count,
        "Relevant Jobs": company.relevant_job_count,
        "Sponsorship Status": company.sponsorship_evidence,
        "Manual Review": company.manual_review_status,
    }
    for company in companies
]

st.sidebar.header("Filters")
tier_filter = st.sidebar.multiselect("Tier", sorted({row["Tier"] for row in company_rows}))
country_filter = st.sidebar.text_input("Country contains")
company_filter = st.sidebar.text_input("Company contains")
segment_filter = st.sidebar.text_input("Battery segment contains")
scan_filter = st.sidebar.multiselect(
    "Scan status", sorted({row["Scan Health"] for row in company_rows})
)

filtered = company_rows
if tier_filter:
    filtered = [row for row in filtered if row["Tier"] in tier_filter]
if country_filter:
    filtered = [row for row in filtered if country_filter.lower() in row["Countries"].lower()]
if company_filter:
    filtered = [row for row in filtered if company_filter.lower() in row["Company"].lower()]
if segment_filter:
    filtered = [row for row in filtered if segment_filter.lower() in row["Battery Segment"].lower()]
if scan_filter:
    filtered = [row for row in filtered if row["Scan Health"] in scan_filter]

st.dataframe(filtered, use_container_width=True, hide_index=True)

st.subheader("Manual Review Queue")
manual_rows = []
for source, company in source_rows:
    if source.status != "manual_review" and company.manual_review_status != "required":
        continue
    retry_count = sum(
        1 for src, c in source_rows if c.id == company.id and src.status == "manual_review"
    )
    suggested = (
        "Check alternate official careers URL, public ATS endpoint, email alert, or manual import."
    )
    if source.http_status == 403:
        suggested = (
            "Do not bypass access controls; find alternate official ATS/careers URL "
            "or use manual/email-alert ingestion."
        )
    elif source.failure_state and "timeout" in source.failure_state.lower():
        suggested = (
            "Retry later with bounded backoff; check regional official careers alternatives."
        )
    manual_rows.append(
        {
            "Company": company.canonical_name,
            "Failed URL": source.source_url,
            "Failure Type": source.failure_state.split(":", 1)[0]
            if source.failure_state
            else source.status,
            "HTTP Status": source.http_status,
            "Last Attempt": source.checked_at,
            "Retry Count": retry_count,
            "Suggested Resolution": suggested,
        }
    )
st.dataframe(manual_rows, use_container_width=True, hide_index=True)

if companies:
    manual_company = st.selectbox(
        "Manual-review action company", [company.canonical_name for company in companies]
    )
    replacement_url = st.text_input("Manual replacement URL")
    col_retry, col_resolve = st.columns(2)
    with col_retry:
        if st.button("Retry Scan"):
            with SessionLocal() as write_session:
                summary = run_watch_scan(write_session, company_names=[manual_company], live=True)
                write_session.commit()
            st.success(f"Retry complete: {summary}")
    with col_resolve:
        if st.button("Mark Resolved"):
            with SessionLocal() as write_session:
                company = write_session.scalar(
                    select(WatchCompany).where(WatchCompany.canonical_name == manual_company)
                )
                if company is not None:
                    if replacement_url:
                        company.official_careers_url = replacement_url
                    company.manual_review_status = "resolved"
                    company.scan_status = "pending"
                    company.updated_at = datetime.now(UTC)
                    write_session.execute(
                        update(WatchJobSource)
                        .where(WatchJobSource.company_id == company.id)
                        .values(status="resolved")
                    )
                    write_session.commit()
            st.success("Manual-review item marked resolved")

selected_company = (
    st.selectbox("Company detail", [row["Company"] for row in company_rows])
    if company_rows
    else None
)
if selected_company:
    company = next(item for item in companies if item.canonical_name == selected_company)
    st.subheader(selected_company)
    left, right = st.columns(2)
    with left:
        st.write(
            {
                "official_careers_link": company.official_careers_url,
                "website": company.company_website,
                "platform": company.careers_platform,
                "ats": company.ats_type,
                "monitoring_frequency": company.preferred_monitoring_frequency,
                "last_verification": company.last_careers_page_verification,
                "last_successful_scan": company.last_successful_scan,
            }
        )
    with right:
        st.write(
            {
                "sponsorship_observations": company.sponsorship_evidence,
                "language_requirements": company.known_language_requirements,
                "manual_review": company.manual_review_status,
                "notes": company.notes,
            }
        )
    company_job_rows = []
    for job, assessment in jobs:
        if job.company_id != company.id:
            continue
        company_job_rows.append(
            {
                "Title": job.title,
                "Location": job.location,
                "Country": job.country,
                "Status": job.active_status,
                "Fit Score": assessment.fit_score if assessment else None,
                "Visa Status": assessment.sponsorship_status if assessment else None,
                "Job Family": assessment.recommended_cv_lane if assessment else None,
                "Action": assessment.recommended_action if assessment else None,
                "URL": job.application_url or job.original_url,
            }
        )
    st.dataframe(company_job_rows, use_container_width=True, hide_index=True)
