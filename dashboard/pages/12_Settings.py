import streamlit as st

from app.core.config import get_settings

st.set_page_config(page_title="Settings", layout="wide")
st.title("Settings")

settings = get_settings()
st.json(
    {
        "env": settings.env,
        "database_url": settings.database_url.replace("///", "///"),
        "max_upload_mb": settings.max_upload_mb,
        "external_writes": "human approval required",
    }
)
