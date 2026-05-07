"""Tests for POST /incidents/{id}/analyze endpoint."""

import os
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

os.environ["RUNGUARD_ANTHROPIC_API_KEY"] = "test-key"
os.environ["RUNGUARD_WEBHOOK_SECRET"] = "test-secret"

from runguard.backend.api.incidents import _incidents, _plans  # noqa: E402
from runguard.backend.main import app  # noqa: E402

client = TestClient(app)


def _create_incident(status: str = "pending") -> str:
    _incidents.clear()
    _plans.clear()
    response = client.post(
        "/incidents",
        json={
            "source": "manual",
            "severity": "critical",
            "environment": "dev",
            "namespace": "default",
            "workload": "my-app",
            "raw_alert": "Pod crash looping",
            "runbook_id": "rb-test",
        },
    )
    inc_id = response.json()["id"]
    _incidents[inc_id]["status"] = status
    return inc_id


def _mock_ai_result():
    return {
        "summary": "OOMKilled causing CrashLoopBackOff",
        "root_causes": [
            {
                "cause": "Memory limit too low",
                "confidence": 0.9,
                "evidence": ["OOMKilled in logs"],
            }
        ],
        "actions": [
            {
                "name": "rollout_restart",
                "target": "my-app",
                "parameters": {},
                "reason": "Restart pods",
            }
        ],
    }


class TestAnalyzeEndpoint:
    def test_analyze_pending_incident(self):
        inc_id = _create_incident("pending")
        with patch(
            "runguard.backend.ai.reasoner.AIReasoner.analyze",
            new_callable=AsyncMock,
            return_value=_mock_ai_result(),
        ):
            response = client.post(f"/incidents/{inc_id}/analyze")
        assert response.status_code == 200
        data = response.json()
        assert data["incident_id"] == inc_id
        assert data["status"] in ("requires_approval", "resolved")
        assert "plan" in data

    def test_analyze_returns_404_for_missing_incident(self):
        response = client.post("/incidents/inc-nonexistent/analyze")
        assert response.status_code == 404

    def test_analyze_returns_400_for_wrong_state(self):
        inc_id = _create_incident("resolved")
        response = client.post(f"/incidents/{inc_id}/analyze")
        assert response.status_code == 400

    def test_analyze_returns_400_for_already_has_plan(self):
        inc_id = _create_incident("requires_approval")
        _plans[inc_id] = {"id": "plan-existing", "actions": [{"id": "act-1"}]}
        response = client.post(f"/incidents/{inc_id}/analyze")
        assert response.status_code == 400

    def test_analyze_creates_plan_with_root_causes(self):
        inc_id = _create_incident("pending")
        with patch(
            "runguard.backend.ai.reasoner.AIReasoner.analyze",
            new_callable=AsyncMock,
            return_value=_mock_ai_result(),
        ):
            response = client.post(f"/incidents/{inc_id}/analyze")
        data = response.json()
        plan = data["plan"]
        assert len(plan["root_causes"]) == 1
        assert plan["root_causes"][0]["confidence"] == 0.9

    def test_analyze_sets_incident_plan_id(self):
        inc_id = _create_incident("pending")
        with patch(
            "runguard.backend.ai.reasoner.AIReasoner.analyze",
            new_callable=AsyncMock,
            return_value=_mock_ai_result(),
        ):
            client.post(f"/incidents/{inc_id}/analyze")
        assert _incidents[inc_id]["plan_id"] is not None
