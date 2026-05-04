"""Tests for runbook API endpoints."""

from fastapi.testclient import TestClient
from runguard.backend.main import app


client = TestClient(app)

SAMPLE_MARKDOWN = """# Test Runbook

## Scope
- Namespaces: default

## Allowed Tools
- rollout restart

## Severity
low

## Rollback Steps
1. kubectl rollout undo deployment/{name}
"""


def test_create_runbook():
    response = client.post(
        "/runbooks",
        json={"title": "Test", "content": SAMPLE_MARKDOWN},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Runbook"
    assert data["id"] is not None


def test_list_runbooks():
    client.post("/runbooks", json={"title": "A", "content": SAMPLE_MARKDOWN})
    client.post("/runbooks", json={"title": "B", "content": SAMPLE_MARKDOWN})

    response = client.get("/runbooks")
    assert response.status_code == 200
    assert len(response.json()) >= 2
