# Architecture

CareerOS starts as a modular monolith with FastAPI, SQLAlchemy, and Streamlit sharing deterministic service modules. External integrations and model providers are isolated behind future adapter interfaces so the local application can run without credentials.
