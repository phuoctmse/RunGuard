"""Tests for API endpoints — edge cases and error handling."""

from fastapi.testclient import TestClient
from runguard.backend.main import app


client = TestClient(app)


# === Health ===

def test_health_endpoint():
    """Health check should return 200 with ok status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# === Incidents ===

def test_get_nonexistent_incident_404():
    """Should return 404 for non-existent incident ID."""
    response = client.get("/incidents/inc-nonexistent-999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Incident not found"


def test_create_incident_returns_all_fields():
    """Should return all incident fields in response."""
    response = client.post(
        "/incidents",
        json={
            "source": "prometheus",
            "severity": "critical",
            "environment": "production",
            "namespace": "prod",
            "workload": "payment-service",
            "raw_alert": "Payment gateway timeout",
        },
    )
    data = response.json()
    assert data["source"] == "prometheus"
    assert data["severity"] == "critical"
    assert data["environment"] == "production"
    assert data["namespace"] == "prod"
    assert data["workload"] == "payment-service"
    assert data["raw_alert"] == "Payment gateway timeout"
    assert data["status"] == "pending"
    assert "created_at" in data
    assert "updated_at" in data


def test_create_incident_empty_strings():
    """Should accept empty string values."""
    response = client.post(
        "/incidents",
        json={
            "source": "",
            "severity": "",
            "environment": "",
            "namespace": "",
            "workload": "",
            "raw_alert": "",
        },
    )
    assert response.status_code == 201


def test_create_incident_special_characters():
    """Should handle special characters in alert text."""
    response = client.post(
        "/incidents",
        json={
            "source": "manual",
            "severity": "high",
            "environment": "dev",
            "namespace": "default",
            "workload": "web-app",
            "raw_alert": "Pod CrashLoopBackOff: error=\"connection refused\" to db:5432 (retries=3/3)",
            "runbook_id": "rb-test",
        },
    )
    assert response.status_code == 201
    assert "connection refused" in response.json()["raw_alert"]


def test_create_incident_unicode():
    """Should handle unicode in alert text."""
    response = client.post(
        "/incidents",
        json={
            "source": "manual",
            "severity": "high",
            "environment": "dev",
            "namespace": "default",
            "workload": "web-app",
            "raw_alert": "Pod sự cố: kết nối thất bại",
            "runbook_id": "rb-test",
        },
    )
    assert response.status_code == 201
    assert "sự cố" in response.json()["raw_alert"]


def test_create_multiple_incidents_unique_ids():
    """Each incident should have a unique ID."""
    ids = set()
    for _ in range(10):
        response = client.post(
            "/incidents",
            json={
                "source": "prometheus",
                "severity": "low",
                "environment": "dev",
                "namespace": "default",
                "workload": "test",
                "raw_alert": "test",
            },
        )
        ids.add(response.json()["id"])
    assert len(ids) == 10


def test_create_incident_missing_source():
    """Should return 422 when source is missing."""
    response = client.post(
        "/incidents",
        json={
            "severity": "high",
            "environment": "dev",
            "namespace": "default",
            "workload": "web-app",
            "raw_alert": "test",
        },
    )
    assert response.status_code == 422


def test_create_incident_extra_fields_ignored():
    """Should ignore extra fields in request."""
    response = client.post(
        "/incidents",
        json={
            "source": "manual",
            "severity": "high",
            "environment": "dev",
            "namespace": "default",
            "workload": "web-app",
            "raw_alert": "test",
            "runbook_id": "rb-test",
            "unknown_field": "should be ignored",
        },
    )
    assert response.status_code == 201


# === Runbooks ===

def test_create_runbook_minimal():
    """Should create runbook with minimal valid markdown."""
    response = client.post(
        "/runbooks",
        json={"title": "Minimal", "content": "# Minimal Runbook\n\n## Severity\nlow\n"},
    )
    assert response.status_code == 201


def test_create_runbook_empty_content():
    """Should handle empty markdown content."""
    response = client.post(
        "/runbooks",
        json={"title": "Empty", "content": ""},
    )
    assert response.status_code == 201


def test_runbook_id_format():
    """Runbook ID should have rb- prefix."""
    response = client.post(
        "/runbooks",
        json={"title": "Test", "content": "# Test\n\n## Severity\nlow\n"},
    )
    assert response.json()["id"].startswith("rb-")


def test_runbook_list_returns_all():
    """List endpoint should return all created runbooks."""
    # Create 3 runbooks
    for i in range(3):
        client.post(
            "/runbooks",
            json={"title": f"Runbook {i}", "content": f"# Runbook {i}\n\n## Severity\nlow\n"},
        )

    response = client.get("/runbooks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3
