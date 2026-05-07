"""Reusable UI components for the RunGuard dashboard."""

from typing import Any

import streamlit as st

# Status color mapping
STATUS_COLORS = {
    "pending": "orange",
    "analyzing": "blue",
    "requires_approval": "red",
    "executing": "blue",
    "resolved": "green",
    "rejected": "gray",
    "failed": "red",
}

STATUS_ICONS = {
    "pending": "⏳",
    "analyzing": "🔍",
    "requires_approval": "⚠️",
    "executing": "⚡",
    "resolved": "✅",
    "rejected": "❌",
    "failed": "💥",
}


def render_status_badge(status: str) -> None:
    """Render a colored status badge."""
    color = STATUS_COLORS.get(status, "gray")
    icon = STATUS_ICONS.get(status, "")
    st.markdown(
        f'<span style="color:{color};font-weight:bold">{icon} {status.upper()}</span>',
        unsafe_allow_html=True,
    )


def render_dry_run_indicator(is_dry_run: bool) -> None:
    """Render a dry-run mode indicator."""
    if is_dry_run:
        st.warning("DRY-RUN MODE — No changes will be applied to the cluster")


def render_incident_card(incident: dict[str, Any]) -> None:
    """Render an incident as a card in the list view."""
    status = incident.get("status", "unknown")
    color = STATUS_COLORS.get(status, "gray")
    icon = STATUS_ICONS.get(status, "")

    with st.container():
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            inc_id = incident.get("id", "N/A")
            workload = incident.get("workload", "Unknown")
            st.markdown(f"**{inc_id}** — {workload}")
            src = incident.get("source", "N/A")
            ns = incident.get("namespace", "N/A")
            st.caption(f"Source: {src} | Namespace: {ns}")
        with col2:
            label = f"{icon} {status.upper()}"
            st.markdown(
                f'<span style="color:{color};font-weight:bold">{label}</span>',
                unsafe_allow_html=True,
            )
        with col3:
            st.caption(incident.get("created_at", ""))
        with col4:
            if st.button("View", key=f"view_{inc_id}"):
                st.query_params["incident_id"] = inc_id
                st.rerun()


def render_approval_buttons(incident_id: str, action_name: str) -> str | None:
    """Render approve/reject buttons for an action.

    Returns:
        "approved" or "rejected" if a button was clicked, None otherwise.
    """
    col1, col2 = st.columns(2)
    result = None
    with col1:
        approve_key = f"approve_{incident_id}_{action_name}"
        if st.button("Approve", key=approve_key, type="primary"):
            result = "approved"
    with col2:
        reject_key = f"reject_{incident_id}_{action_name}"
        if st.button("Reject", key=reject_key, type="secondary"):
            result = "rejected"
    return result


def render_evidence_section(evidence: dict[str, Any]) -> None:
    """Render evidence collected for an incident."""
    if not evidence:
        st.info("No evidence collected")
        return

    if evidence.get("pod_logs"):
        st.subheader("Pod Logs")
        for pod_name, logs in evidence["pod_logs"].items():
            with st.expander(f"Pod: {pod_name}"):
                st.code(logs[:2000], language="text")

    if evidence.get("events"):
        st.subheader("Kubernetes Events")
        for event in evidence["events"][:20]:
            st.markdown(
                f"- **{event.get('reason', 'N/A')}** ({event.get('type', '')}): "
                f"{event.get('message', '')}"
            )

    if evidence.get("deployment_status"):
        st.subheader("Deployment Status")
        status = evidence["deployment_status"]
        if "error" not in status:
            col1, col2, col3 = st.columns(3)
            col1.metric("Desired", status.get("desired_replicas", "N/A"))
            col2.metric("Ready", status.get("ready_replicas", "N/A"))
            col3.metric("Available", status.get("available_replicas", "N/A"))
        else:
            st.error(status["error"])


def render_remediation_plan(plan: dict[str, Any]) -> None:
    """Render a remediation plan."""
    if not plan:
        st.info("No remediation plan available")
        return

    if plan.get("summary"):
        st.markdown(f"**Summary:** {plan['summary']}")

    if plan.get("root_causes"):
        st.subheader("Root Causes")
        for rc in plan["root_causes"]:
            confidence = rc.get("confidence", 0)
            st.markdown(
                f"- **{rc.get('cause', 'Unknown')}** (confidence: {confidence:.0%})"
            )
            if rc.get("evidence_refs"):
                for ref in rc["evidence_refs"]:
                    st.caption(f"  Evidence: {ref}")

    if plan.get("remediation_actions"):
        st.subheader("Proposed Actions")
        for action in plan["remediation_actions"]:
            action_name = action.get("action", "N/A")
            target = action.get("target", "N/A")
            priority = action.get("priority", "N/A")
            st.markdown(f"1. **{action_name}** → `{target}` (Priority: {priority})")
            st.caption(f"   Reason: {action.get('reason', '')}")


def render_timeline(timeline_events: list[dict[str, Any]]) -> None:
    """Render an incident timeline."""
    if not timeline_events:
        st.info("No timeline events")
        return

    for event in timeline_events:
        timestamp = event.get("timestamp", "N/A")
        event_type = event.get("event_type", "N/A")
        details = event.get("details", {})
        st.markdown(f"**{timestamp}** — `{event_type}`")
        if details:
            st.json(details)


def render_cost_display(cost_data: dict[str, Any]) -> None:
    """Render cost information."""
    if not cost_data:
        return

    col1, col2 = st.columns(2)
    with col1:
        total = cost_data.get("total_cost", 0)
        st.metric("Infrastructure Cost", f"${total:.2f}")
    with col2:
        est = cost_data.get("estimated_action_cost", 0)
        st.metric("Estimated Action Cost", f"${est:.4f}")
