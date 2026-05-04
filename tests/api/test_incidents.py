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
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["status"] == "pending"


def test_create_incident_missing_fields():
    response = client.post(
        "/incidents",
        json={"source": "manual"},
    )
    assert response.status_code == 422


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
        },
    )
    incident_id = create_response.json()["id"]

    response = client.get(f"/incidents/{incident_id}")
    assert response.status_code == 200
    assert response.json()["id"] == incident_id
