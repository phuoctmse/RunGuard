"""Page components for the RunGuard dashboard."""

from typing import Any

import httpx
import streamlit as st

from runguard.ui.components import (
    render_approval_buttons,
    render_dry_run_indicator,
    render_incident_card,
    render_remediation_plan,
    render_status_badge,
    render_timeline,
)

# Default API base URL
DEFAULT_API_URL = "http://localhost:8000"


def _api_url() -> str:
    """Get the API base URL from session state or default."""
    return str(st.session_state.get("api_url", DEFAULT_API_URL))


def _api_get(path: str) -> Any:
    """Make a GET request to the API."""
    try:
        response = httpx.get(f"{_api_url()}{path}", timeout=10.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return {}


def _api_post(path: str, data: dict[str, Any] | None = None) -> Any:
    """Make a POST request to the API."""
    try:
        response = httpx.post(f"{_api_url()}{path}", json=data or {}, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return {}


def render_incident_list_page() -> None:
    """Render the incident list page."""
    st.title("Incidents")
    render_dry_run_indicator(st.session_state.get("dry_run", False))

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            [
                "All", "pending", "analyzing", "requires_approval",
                "executing", "resolved", "rejected", "failed",
            ],
        )
    with col2:
        severity_filter = st.selectbox(
            "Filter by Severity",
            ["All", "low", "medium", "high", "critical"],
        )

    # Fetch incidents
    data = _api_get("/incidents")
    incidents = data if isinstance(data, list) else data.get("incidents", [])

    # Apply filters
    if status_filter != "All":
        incidents = [i for i in incidents if i.get("status") == status_filter]
    if severity_filter != "All":
        incidents = [i for i in incidents if i.get("severity") == severity_filter]

    if not incidents:
        st.info("No incidents found")
        return

    for incident in incidents:
        render_incident_card(incident)
        st.divider()


def render_incident_detail_page(incident_id: str) -> None:
    """Render the incident detail page."""
    st.title(f"Incident: {incident_id}")

    # Fetch incident details
    incident = _api_get(f"/incidents/{incident_id}")
    if not incident or "error" in incident:
        st.error("Incident not found")
        return

    # Status and metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**Source:** {incident.get('source', 'N/A')}")
        st.markdown(f"**Namespace:** {incident.get('namespace', 'N/A')}")
    with col2:
        st.markdown(f"**Workload:** {incident.get('workload', 'N/A')}")
        st.markdown(f"**Severity:** {incident.get('severity', 'N/A')}")
    with col3:
        render_status_badge(incident.get("status", "unknown"))
        st.caption(f"Created: {incident.get('created_at', 'N/A')}")

    st.divider()

    # Fetch plan
    plan = _api_get(f"/incidents/{incident_id}/plan")
    render_remediation_plan(plan if isinstance(plan, dict) else {})

    st.divider()

    # Approval section
    if incident.get("status") == "requires_approval":
        st.subheader("Approval Required")
        actions = plan.get("remediation_actions", []) if isinstance(plan, dict) else []
        for action in actions:
            action_name = action.get("action", "unknown")
            st.markdown(f"**Action:** {action_name} → {action.get('target', 'N/A')}")
            result = render_approval_buttons(incident_id, action_name)
            if result == "approved":
                _api_post(f"/incidents/{incident_id}/approve")
                st.success("Action approved!")
                st.rerun()
            elif result == "rejected":
                _api_post(f"/incidents/{incident_id}/reject")
                st.warning("Action rejected")
                st.rerun()

    # Audit trail
    st.divider()
    st.subheader("Audit Trail")
    audit = _api_get(f"/audit/{incident_id}")
    if isinstance(audit, list):
        render_timeline(audit)
    else:
        render_timeline(audit.get("records", []))


def render_runbooks_page() -> None:
    """Render the runbooks list page."""
    st.title("Runbooks")

    data = _api_get("/runbooks")
    runbooks = data if isinstance(data, list) else data.get("runbooks", [])

    if not runbooks:
        st.info("No runbooks found")
        return

    for rb in runbooks:
        with st.container():
            st.markdown(f"**{rb.get('title', 'Untitled')}**")
            rb_id = rb.get("id", "N/A")
            rb_ver = rb.get("version", "N/A")
            st.caption(f"ID: {rb_id} | Version: {rb_ver}")
            if rb.get("scope"):
                st.markdown(f"Scope: `{rb['scope']}`")
            st.divider()


def render_settings_page() -> None:
    """Render the settings page."""
    st.title("Settings")

    st.session_state["api_url"] = st.text_input(
        "API URL",
        value=st.session_state.get("api_url", DEFAULT_API_URL),
    )

    st.session_state["dry_run"] = st.checkbox(
        "Dry-Run Mode",
        value=st.session_state.get("dry_run", False),
    )

    st.divider()
    st.subheader("System Status")
    health = _api_get("/health")
    if health.get("status") == "ok":
        st.success("API is healthy")
    else:
        st.error("API is unreachable")
