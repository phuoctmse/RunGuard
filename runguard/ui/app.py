"""RunGuard Streamlit dashboard — main entry point."""

import streamlit as st

from runguard.ui.pages import (
    render_incident_detail_page,
    render_incident_list_page,
    render_runbooks_page,
    render_settings_page,
)

st.set_page_config(
    page_title="RunGuard Dashboard",
    page_icon="🛡️",
    layout="wide",
)

# Initialize session state defaults
if "api_url" not in st.session_state:
    st.session_state["api_url"] = "http://localhost:8000"
if "dry_run" not in st.session_state:
    st.session_state["dry_run"] = False

# Sidebar navigation
st.sidebar.title("RunGuard")
st.sidebar.markdown("AI-powered incident remediation")

page = st.sidebar.radio(
    "Navigation",
    ["Incidents", "Runbooks", "Settings"],
)

# Check for incident ID in query params
query_params = st.query_params
incident_id = query_params.get("incident_id")

if page == "Incidents":
    if incident_id:
        render_incident_detail_page(incident_id)
    else:
        render_incident_list_page()
elif page == "Runbooks":
    render_runbooks_page()
elif page == "Settings":
    render_settings_page()

# Footer
st.sidebar.divider()
st.sidebar.caption("RunGuard v0.1.0 — Phase 4")
