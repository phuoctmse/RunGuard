"""Tests for POST /incidents/{id}/execute endpoint."""

import os
from unittest.mock import patch

from fastapi.testclient import TestClient

os.environ["RUNGUARD_ANTHROPIC_API_KEY"] = "test-key"
os.environ["RUNGUARD_WEBHOOK_SECRET"] = "test-secret"

from runguard.backend.api.incidents import _incidents, _plans
from runguard.backend.main import app

client = TestClient(app)


def _create_incident_with_plan(status: str = "approved") -> tuple[str, str]:
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
    _incidents[inc_id]["status"] = status

    plan_id = "plan-test"
    action_id = "act-test"
    _plans[inc_id] = {
        "id": plan_id,
        "incident_id": inc_id,
        "summary": "Test plan",
        "root_causes": [],
        "actions": [
            {
                "id": action_id,
                "plan_id": plan_id,
                "name": "rollout_restart",
                "target": "my-app",
                "namespace": "default",
                "parameters": {},
                "blast_radius": "low",
                "rollback_path": "manual rollback",
                "status": "approved",
                "policy_decision": "approved",
                "policy_reason": "Low risk",
            }
        ],
    }
    return inc_id, action_id


class TestExecuteEndpoint:
    def test_execute_approved_incident(self):
        inc_id, _ = _create_incident_with_plan("approved")
        with patch(
            "runguard.backend.executor.actions._execute",
            return_value={
                "action": "rollout_restart",
                "status": "completed",
                "output": "deployment/my-app restarted",
                "error": "",
            },
        ):
            response = client.post(f"/incidents/{inc_id}/execute")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "resolved"
        assert len(data["results"]) == 1
        assert data["results"][0]["status"] == "completed"

    def test_execute_returns_404_for_missing(self):
        response = client.post("/incidents/inc-nonexistent/execute")
        assert response.status_code == 404

    def test_execute_returns_400_for_wrong_state(self):
        inc_id, _ = _create_incident_with_plan("pending")
        response = client.post(f"/incidents/{inc_id}/execute")
        assert response.status_code == 400

    def test_execute_partial_failure_returns_207(self):
        inc_id, _ = _create_incident_with_plan("approved")
        _plans[inc_id]["actions"].append(
            {
                "id": "act-fail",
                "plan_id": "plan-test",
                "name": "scale_replicas",
                "target": "missing-app",
                "namespace": "default",
                "parameters": {"replicas": 3},
                "blast_radius": "medium",
                "rollback_path": "",
                "status": "approved",
                "policy_decision": "approved",
                "policy_reason": "",
            }
        )

        call_count = [0]

        def mock_execute_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return {
                    "action": "rollout_restart",
                    "status": "completed",
                    "output": "restarted",
                    "error": "",
                }
            return {
                "action": "scale_replicas",
                "status": "failed",
                "output": "",
                "error": "deployment not found",
            }

        with patch(
            "runguard.backend.executor.actions._execute",
            side_effect=mock_execute_side_effect,
        ):
            response = client.post(f"/incidents/{inc_id}/execute")
        assert response.status_code == 207
        data = response.json()
        assert data["status"] == "failed"

    def test_execute_skips_blocked_actions(self):
        inc_id, _ = _create_incident_with_plan("approved")
        _plans[inc_id]["actions"].append(
            {
                "id": "act-blocked",
                "plan_id": "plan-test",
                "name": "delete_pod",
                "target": "my-app",
                "namespace": "default",
                "parameters": {},
                "blast_radius": "high",
                "rollback_path": "",
                "status": "pending",
                "policy_decision": "blocked",
                "policy_reason": "Forbidden",
            }
        )

        with patch(
            "runguard.backend.executor.actions._execute",
            return_value={
                "action": "rollout_restart",
                "status": "completed",
                "output": "restarted",
                "error": "",
            },
        ):
            response = client.post(f"/incidents/{inc_id}/execute")
        data = response.json()
        assert len(data["results"]) == 1

    def test_execute_sets_resolved_on_success(self):
        inc_id, _ = _create_incident_with_plan("approved")
        with patch(
            "runguard.backend.executor.actions._execute",
            return_value={
                "action": "rollout_restart",
                "status": "completed",
                "output": "ok",
                "error": "",
            },
        ):
            client.post(f"/incidents/{inc_id}/execute")
        assert _incidents[inc_id]["status"] == "resolved"
