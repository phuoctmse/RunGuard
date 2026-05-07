"""Tests for Slack notifications wired into the execute endpoint."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

os.environ["RUNGUARD_ANTHROPIC_API_KEY"] = "test-key"
os.environ["RUNGUARD_WEBHOOK_SECRET"] = "test-secret"
os.environ["RUNGUARD_SLACK_WEBHOOK_URL"] = "https://hooks.slack.com/test"

from runguard.backend.api.incidents import _incidents, _plans
from runguard.backend.notifications.slack import SlackNotifier
from runguard.backend.main import app

client = TestClient(app)


def _create_approved_incident():
    _incidents.clear()
    _plans.clear()
    response = client.post(
        "/incidents",
        json={
            "source": "manual",
            "severity": "high",
            "environment": "dev",
            "namespace": "default",
            "workload": "my-app",
            "raw_alert": "test",
            "runbook_id": "rb-test",
        },
    )
    inc_id = response.json()["id"]
    _incidents[inc_id]["status"] = "approved"
    _plans[inc_id] = {
        "id": "plan-test",
        "incident_id": inc_id,
        "summary": "Test plan",
        "root_causes": [],
        "actions": [
            {
                "id": "act-1",
                "plan_id": "plan-test",
                "name": "rollout_restart",
                "target": "my-app",
                "namespace": "default",
                "parameters": {},
                "blast_radius": "low",
                "rollback_path": "manual",
                "status": "approved",
                "policy_decision": "approved",
                "policy_reason": "",
            }
        ],
    }
    return inc_id


def _make_mock_slack():
    """Create a mock SlackNotifier with async methods."""
    mock = MagicMock(spec=SlackNotifier)
    mock.send_action_executed = AsyncMock()
    mock.send_action_failed = AsyncMock()
    mock.send_resolved = AsyncMock()
    return mock


class TestExecuteNotifications:
    def test_execute_sends_slack_notification(self):
        inc_id = _create_approved_incident()
        mock_slack = _make_mock_slack()
        with (
            patch("runguard.backend.executor.actions._execute", return_value={
                "action": "rollout_restart",
                "status": "completed",
                "output": "restarted",
                "error": "",
            }),
            patch("runguard.backend.api.incidents._get_slack", return_value=mock_slack),
        ):
            client.post(f"/incidents/{inc_id}/execute")
        mock_slack.send_action_executed.assert_called_once()

    def test_execute_sends_failure_notification(self):
        inc_id = _create_approved_incident()
        mock_slack = _make_mock_slack()
        with (
            patch("runguard.backend.executor.actions._execute", return_value={
                "action": "rollout_restart",
                "status": "failed",
                "output": "",
                "error": "not found",
            }),
            patch("runguard.backend.api.incidents._get_slack", return_value=mock_slack),
        ):
            client.post(f"/incidents/{inc_id}/execute")
        mock_slack.send_action_failed.assert_called_once()

    def test_execute_sends_resolved_notification(self):
        inc_id = _create_approved_incident()
        mock_slack = _make_mock_slack()
        with (
            patch("runguard.backend.executor.actions._execute", return_value={
                "action": "rollout_restart",
                "status": "completed",
                "output": "restarted",
                "error": "",
            }),
            patch("runguard.backend.api.incidents._get_slack", return_value=mock_slack),
        ):
            client.post(f"/incidents/{inc_id}/execute")
        mock_slack.send_resolved.assert_called_once()

    def test_execute_no_resolved_on_failure(self):
        inc_id = _create_approved_incident()
        mock_slack = _make_mock_slack()
        with (
            patch("runguard.backend.executor.actions._execute", return_value={
                "action": "rollout_restart",
                "status": "failed",
                "output": "",
                "error": "not found",
            }),
            patch("runguard.backend.api.incidents._get_slack", return_value=mock_slack),
        ):
            client.post(f"/incidents/{inc_id}/execute")
        mock_slack.send_resolved.assert_not_called()

    def test_execute_no_slack_when_none(self):
        """When _get_slack returns None (no webhook configured), execution still works."""
        inc_id = _create_approved_incident()
        with (
            patch("runguard.backend.executor.actions._execute", return_value={
                "action": "rollout_restart",
                "status": "completed",
                "output": "restarted",
                "error": "",
            }),
            patch("runguard.backend.api.incidents._get_slack", return_value=None),
        ):
            response = client.post(f"/incidents/{inc_id}/execute")
        assert response.status_code == 200
