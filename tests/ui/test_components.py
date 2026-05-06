"""Tests for UI components."""

from unittest.mock import MagicMock, patch

import pytest

from runguard.ui.components import (
    STATUS_COLORS,
    STATUS_ICONS,
    render_approval_buttons,
    render_cost_display,
    render_dry_run_indicator,
    render_evidence_section,
    render_incident_card,
    render_remediation_plan,
    render_status_badge,
    render_timeline,
)


def test_status_colors_cover_all_statuses():
    expected = {"pending", "analyzing", "requires_approval", "executing", "resolved", "rejected", "failed"}
    assert set(STATUS_COLORS.keys()) == expected


def test_status_icons_cover_all_statuses():
    assert set(STATUS_ICONS.keys()) == set(STATUS_COLORS.keys())


@patch("runguard.ui.components.st")
def test_render_status_badge(mock_st):
    render_status_badge("pending")
    mock_st.markdown.assert_called_once()
    call_args = mock_st.markdown.call_args
    assert "PENDING" in call_args[0][0]


@patch("runguard.ui.components.st")
def test_render_dry_run_indicator_active(mock_st):
    render_dry_run_indicator(True)
    mock_st.warning.assert_called_once()
    assert "DRY-RUN" in mock_st.warning.call_args[0][0]


@patch("runguard.ui.components.st")
def test_render_dry_run_indicator_inactive(mock_st):
    render_dry_run_indicator(False)
    mock_st.warning.assert_not_called()


@patch("runguard.ui.components.st")
def test_render_incident_card(mock_st):
    mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
    incident = {
        "id": "inc-001",
        "workload": "my-app",
        "source": "prometheus",
        "namespace": "default",
        "status": "pending",
        "created_at": "2024-01-01T00:00:00",
    }
    render_incident_card(incident)
    mock_st.container.assert_called_once()


@patch("runguard.ui.components.st")
def test_render_approval_buttons(mock_st):
    mock_st.columns.return_value = [MagicMock(), MagicMock()]
    mock_st.button.return_value = False
    result = render_approval_buttons("inc-001", "rollout_restart")
    assert result is None


@patch("runguard.ui.components.st")
def test_render_approval_buttons_approve(mock_st):
    mock_st.columns.return_value = [MagicMock(), MagicMock()]
    mock_st.button.side_effect = [True, False]
    result = render_approval_buttons("inc-001", "rollout_restart")
    assert result == "approved"


@patch("runguard.ui.components.st")
def test_render_approval_buttons_reject(mock_st):
    mock_st.columns.return_value = [MagicMock(), MagicMock()]
    mock_st.button.side_effect = [False, True]
    result = render_approval_buttons("inc-001", "rollout_restart")
    assert result == "rejected"


@patch("runguard.ui.components.st")
def test_render_evidence_empty(mock_st):
    render_evidence_section({})
    mock_st.info.assert_called_once()


@patch("runguard.ui.components.st")
def test_render_evidence_with_logs(mock_st):
    mock_st.expander.return_value.__enter__ = MagicMock()
    mock_st.expander.return_value.__exit__ = MagicMock()
    evidence = {
        "pod_logs": {"pod-1": "log line 1\nlog line 2"},
        "events": [],
        "deployment_status": {},
    }
    render_evidence_section(evidence)
    mock_st.subheader.assert_called()


@patch("runguard.ui.components.st")
def test_render_evidence_with_deployment_status(mock_st):
    mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
    evidence = {
        "pod_logs": {},
        "events": [],
        "deployment_status": {
            "desired_replicas": 3,
            "ready_replicas": 3,
            "available_replicas": 3,
        },
    }
    render_evidence_section(evidence)
    mock_st.subheader.assert_called()


@patch("runguard.ui.components.st")
def test_render_remediation_plan_empty(mock_st):
    render_remediation_plan({})
    mock_st.info.assert_called_once()


@patch("runguard.ui.components.st")
def test_render_remediation_plan_with_data(mock_st):
    plan = {
        "summary": "Pod crash loop detected",
        "root_causes": [
            {"cause": "Bad env var", "confidence": 0.85, "evidence_refs": ["log line 1"]}
        ],
        "remediation_actions": [
            {"action": "rollout_restart", "target": "my-app", "priority": 1, "reason": "Reset pods"}
        ],
    }
    render_remediation_plan(plan)
    mock_st.markdown.assert_called()
    mock_st.subheader.assert_called()


@patch("runguard.ui.components.st")
def test_render_timeline_empty(mock_st):
    render_timeline([])
    mock_st.info.assert_called_once()


@patch("runguard.ui.components.st")
def test_render_timeline_with_events(mock_st):
    events = [
        {"timestamp": "2024-01-01T00:00:00", "event_type": "incident_created", "details": {"source": "prometheus"}},
        {"timestamp": "2024-01-01T00:01:00", "event_type": "plan_generated", "details": {}},
    ]
    render_timeline(events)
    assert mock_st.markdown.call_count == 2


@patch("runguard.ui.components.st")
def test_render_cost_display(mock_st):
    mock_st.columns.return_value = [MagicMock(), MagicMock()]
    cost_data = {"total_cost": 1.23, "estimated_action_cost": 0.05}
    render_cost_display(cost_data)
    assert mock_st.metric.call_count == 2


@patch("runguard.ui.components.st")
def test_render_cost_display_empty(mock_st):
    render_cost_display({})
    mock_st.metric.assert_not_called()
