import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import select

from app.db.base import SessionLocal
from app.models.entities import JobFitAssessment

st.set_page_config(page_title="Analytics", layout="wide")
st.title("Analytics")

with SessionLocal() as session:
    scores = list(session.scalars(select(JobFitAssessment)))

data = pd.DataFrame(
    [{"score": score.total_score, "recommendation": score.recommendation} for score in scores]
)
if data.empty:
    st.info("No scored jobs yet.")
else:
    st.plotly_chart(px.histogram(data, x="score", color="recommendation"), use_container_width=True)
    st.dataframe(data, use_container_width=True, hide_index=True)
