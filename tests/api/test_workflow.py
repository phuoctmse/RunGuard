"""Tests for workflow API endpoints."""

from fastapi.testclient import TestClient

from runguard.backend.main import app

client = TestClient(app)


def test_approve_action():
    response = client.post(
        "/incidents/test-001/approve", json={"approver": "john"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "approved"


def test_reject_action():
    response = client.post(
        "/incidents/test-002/reject",
        json={"rejector": "jane", "reason": "too risky"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
