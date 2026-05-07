"""Tests for incident API endpoints."""

import pytest
from fastapi.testclient import TestClient
from runguard.backend.main import app


client = TestClient(app)


def test_create_incident():
    response = client.post(
        "/incidents",
        json={
            "source": "manual",
            "severity": "high",
            "environment": "dev",
            "namespace": "default",
            "workload": "web-app",
            "raw_alert": "Pod CrashLoopBackOff",
            "runbook_id": "rb-test",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["status"] == "pending"
    assert data["runbook_id"] == "rb-test"


def test_create_incident_missing_fields():
    response = client.post(
        "/incidents",
        json={"source": "manual"},
    )
    assert response.status_code == 422


def test_create_manual_incident_without_runbook_id():
    """Manual incidents without runbook_id should be rejected."""
    response = client.post(
        "/incidents",
        json={
            "source": "manual",
            "severity": "high",
            "environment": "dev",
            "namespace": "default",
            "workload": "web-app",
            "raw_alert": "test",
        },
    )
    assert response.status_code == 400
    assert "runbook_id" in response.json()["detail"]


def test_create_webhook_incident_without_runbook_id():
    """Webhook incidents (non-manual) should not require runbook_id."""
    response = client.post(
        "/incidents",
        json={
            "source": "prometheus",
            "severity": "high",
            "environment": "dev",
            "namespace": "default",
            "workload": "web-app",
            "raw_alert": "test",
        },
    )
    assert response.status_code == 201
    assert response.json()["runbook_id"] is None


def test_get_incident():
    # Create first
    create_response = client.post(
        "/incidents",
        json={
            "source": "manual",
            "severity": "medium",
            "environment": "dev",
            "namespace": "default",
            "workload": "api",
            "raw_alert": "High latency",
            "runbook_id": "rb-test",
        },
    )
    incident_id = create_response.json()["id"]

    response = client.get(f"/incidents/{incident_id}")
    assert response.status_code == 200
    assert response.json()["id"] == incident_id
