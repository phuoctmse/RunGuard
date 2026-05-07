"""Tests for workflow API endpoints."""

from fastapi.testclient import TestClient

from runguard.backend.api.incidents import _incidents, _plans
from runguard.backend.main import app

client = TestClient(app)


def _create_incident_in_state(status: str) -> str:
    """Helper to create an incident and set it to a specific status."""
    response = client.post(
        "/incidents",
        json={
            "source": "prometheus",
            "severity": "high",
            "environment": "production",
            "namespace": "default",
            "workload": "web-app",
            "raw_alert": "test alert",
        },
    )
    incident_id = response.json()["id"]
    _incidents[incident_id]["status"] = status
    return incident_id


def test_approve_action():
    incident_id = _create_incident_in_state("requires_approval")
    response = client.post(
        f"/incidents/{incident_id}/approve", json={"approver": "john"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "approved"


def test_reject_action():
    incident_id = _create_incident_in_state("requires_approval")
    response = client.post(
        f"/incidents/{incident_id}/reject",
        json={"rejector": "jane", "reason": "too risky"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"


def test_approve_nonexistent_incident():
    """Should return 404 for non-existent incident."""
    response = client.post("/incidents/inc-nonexistent/approve")
    assert response.status_code == 404


def test_approve_wrong_state():
    """Should return 400 if incident is not in requires_approval state."""
    incident_id = _create_incident_in_state("pending")
    response = client.post(f"/incidents/{incident_id}/approve")
    assert response.status_code == 400
    assert "requires_approval" in response.json()["detail"]


def test_reject_wrong_state():
    """Should return 400 if incident is not in requires_approval state."""
    incident_id = _create_incident_in_state("resolved")
    response = client.post(f"/incidents/{incident_id}/reject")
    assert response.status_code == 400
    assert "requires_approval" in response.json()["detail"]


# === Blocked actions behavior ===


def test_approve_skips_blocked_actions():
    """Blocked actions should be skipped, not approved."""
    incident_id = _create_incident_in_state("requires_approval")
    _plans[incident_id] = {
        "id": f"plan-{incident_id}",
        "incident_id": incident_id,
        "actions": [
            {
                "id": "act-1",
                "name": "rollout_restart",
                "target": "web-app",
                "status": "pending",
                "policy_decision": "requires_approval",
            },
            {
                "id": "act-2",
                "name": "delete_deployment",
                "target": "web-app",
                "status": "blocked",
                "policy_decision": "blocked",
            },
        ],
    }

    response = client.post(f"/incidents/{incident_id}/approve")
    assert response.status_code == 200
    assert response.json()["status"] == "approved"

    # Verify: requires_approval action was approved, blocked action stays blocked
    actions = _plans[incident_id]["actions"]
    assert actions[0]["status"] == "approved"
    assert actions[1]["status"] == "blocked"

    # Cleanup
    del _plans[incident_id]


def test_approve_all_blocked_actions_fails_incident():
    """If all actions are blocked, incident should fail."""
    incident_id = _create_incident_in_state("requires_approval")
    _plans[incident_id] = {
        "id": f"plan-{incident_id}",
        "incident_id": incident_id,
        "actions": [
            {
                "id": "act-1",
                "name": "delete_deployment",
                "target": "web-app",
                "status": "blocked",
                "policy_decision": "blocked",
            },
            {
                "id": "act-2",
                "name": "delete_namespace",
                "target": "default",
                "status": "blocked",
                "policy_decision": "blocked",
            },
        ],
    }

    response = client.post(f"/incidents/{incident_id}/approve")
    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert _incidents[incident_id]["status"] == "failed"

    # Cleanup
    del _plans[incident_id]


def test_approve_without_plan():
    """Approve without a plan should still work (pre-AI-analysis flow)."""
    incident_id = _create_incident_in_state("requires_approval")
    response = client.post(f"/incidents/{incident_id}/approve")
    assert response.status_code == 200
    assert response.json()["status"] == "approved"


# === Per-action approval ===


def test_approve_single_action():
    """Should approve a single action by ID."""
    incident_id = _create_incident_in_state("requires_approval")
    _plans[incident_id] = {
        "id": f"plan-{incident_id}",
        "incident_id": incident_id,
        "actions": [
            {
                "id": "act-1",
                "name": "rollout_restart",
                "target": "web-app",
                "status": "pending",
                "policy_decision": "requires_approval",
            },
            {
                "id": "act-2",
                "name": "scale_replicas",
                "target": "web-app",
                "status": "pending",
                "policy_decision": "requires_approval",
            },
        ],
    }

    response = client.post(f"/incidents/{incident_id}/actions/act-1/approve")
    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert _plans[incident_id]["actions"][0]["status"] == "approved"
    # act-2 should still be pending
    assert _plans[incident_id]["actions"][1]["status"] == "pending"
    # Incident should still be requires_approval (not all actions approved)
    assert _incidents[incident_id]["status"] == "requires_approval"

    del _plans[incident_id]


def test_approve_single_action_auto_transitions_incident():
    """When all requires_approval actions are approved, incident should auto-transition."""
    incident_id = _create_incident_in_state("requires_approval")
    _plans[incident_id] = {
        "id": f"plan-{incident_id}",
        "incident_id": incident_id,
        "actions": [
            {
                "id": "act-1",
                "name": "rollout_restart",
                "target": "web-app",
                "status": "pending",
                "policy_decision": "requires_approval",
            },
        ],
    }

    response = client.post(f"/incidents/{incident_id}/actions/act-1/approve")
    assert response.status_code == 200
    assert _incidents[incident_id]["status"] == "approved"

    del _plans[incident_id]


def test_approve_single_action_blocked():
    """Should return 400 when trying to approve a blocked action."""
    incident_id = _create_incident_in_state("requires_approval")
    _plans[incident_id] = {
        "id": f"plan-{incident_id}",
        "incident_id": incident_id,
        "actions": [
            {
                "id": "act-1",
                "name": "delete_deployment",
                "target": "web-app",
                "status": "blocked",
                "policy_decision": "blocked",
                "policy_reason": "Forbidden by runbook",
            },
        ],
    }

    response = client.post(f"/incidents/{incident_id}/actions/act-1/approve")
    assert response.status_code == 400
    assert "blocked" in response.json()["detail"]

    del _plans[incident_id]


def test_approve_single_action_already_approved():
    """Should return already_approved for already-approved action."""
    incident_id = _create_incident_in_state("requires_approval")
    _plans[incident_id] = {
        "id": f"plan-{incident_id}",
        "incident_id": incident_id,
        "actions": [
            {
                "id": "act-1",
                "name": "rollout_restart",
                "target": "web-app",
                "status": "approved",
                "policy_decision": "requires_approval",
            },
        ],
    }

    response = client.post(f"/incidents/{incident_id}/actions/act-1/approve")
    assert response.status_code == 200
    assert response.json()["status"] == "already_approved"

    del _plans[incident_id]


def test_approve_single_action_not_found():
    """Should return 404 for non-existent action."""
    incident_id = _create_incident_in_state("requires_approval")
    _plans[incident_id] = {
        "id": f"plan-{incident_id}",
        "incident_id": incident_id,
        "actions": [],
    }

    response = client.post(f"/incidents/{incident_id}/actions/act-nonexistent/approve")
    assert response.status_code == 404

    del _plans[incident_id]


def test_approve_single_action_wrong_incident_state():
    """Should return 400 if incident is not in requires_approval state."""
    incident_id = _create_incident_in_state("pending")
    response = client.post(f"/incidents/{incident_id}/actions/act-1/approve")
    assert response.status_code == 400
    assert "requires_approval" in response.json()["detail"]
