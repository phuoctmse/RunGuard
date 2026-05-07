"""Integration test for Phase 5: Webhook → Analyze → Approve → Execute flow."""

import os
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

os.environ["RUNGUARD_ANTHROPIC_API_KEY"] = "test-key"
os.environ["RUNGUARD_WEBHOOK_SECRET"] = "test-secret"
os.environ["RUNGUARD_SLACK_WEBHOOK_URL"] = ""

from runguard.backend.api.incidents import _incidents, _plans
from runguard.backend.main import app

client = TestClient(app)

WEBHOOK_PAYLOAD = {
    "alerts": [
        {
            "status": "firing",
            "labels": {
                "alertname": "PodCrashLooping",
                "namespace": "default",
                "pod": "my-app-xxx",
                "severity": "critical",
            },
            "annotations": {
                "summary": "Pod crash looping",
                "description": "5 restarts in 10 min",
            },
        }
    ]
}


def _ai_result():
    return {
        "summary": "Pod CrashLoopBackOff due to OOMKilled",
        "root_causes": [
            {
                "cause": "Memory limit too low",
                "confidence": 0.92,
                "evidence": ["OOMKilled in pod logs"],
            }
        ],
        "actions": [
            {
                "name": "rollout_restart",
                "target": "my-app",
                "parameters": {},
                "reason": "Restart to clear CrashLoop",
            }
        ],
    }


class TestPhase5Integration:
    @patch("runguard.backend.api.webhooks.settings")
    def test_full_webhook_to_resolved_flow(self, mock_settings):
        """Webhook → pending → analyze → requires_approval → approve → approved → execute → resolved."""
        mock_settings.webhook_secret = "test-secret"
        _incidents.clear()
        _plans.clear()

        # Step 1: Webhook creates incident
        webhook_response = client.post(
            "/webhooks/alertmanager",
            json=WEBHOOK_PAYLOAD,
            headers={"Authorization": "Bearer test-secret"},
        )
        assert webhook_response.status_code == 200
        inc_id = webhook_response.json()["incident_ids"][0]
        assert _incidents[inc_id]["status"] == "pending"

        # Step 2: Analyze with mocked AI
        with patch(
            "runguard.backend.ai.reasoner.AIReasoner.analyze",
            new_callable=AsyncMock,
            return_value=_ai_result(),
        ):
            analyze_response = client.post(f"/incidents/{inc_id}/analyze")
        assert analyze_response.status_code == 200
        assert _incidents[inc_id]["status"] == "requires_approval"
        assert _incidents[inc_id]["plan_id"] is not None

        # Step 3: Approve
        approve_response = client.post(f"/incidents/{inc_id}/approve")
        assert approve_response.status_code == 200
        assert _incidents[inc_id]["status"] == "approved"

        # Step 4: Execute
        with patch(
            "runguard.backend.executor.actions._execute",
            return_value={
                "action": "rollout_restart",
                "status": "completed",
                "output": "deployment/my-app restarted",
                "error": "",
            },
        ):
            execute_response = client.post(f"/incidents/{inc_id}/execute")
        assert execute_response.status_code == 200
        assert execute_response.json()["status"] == "resolved"
        assert _incidents[inc_id]["status"] == "resolved"

    def test_manual_incident_flow(self):
        """Manual create → analyze → check status."""
        _incidents.clear()
        _plans.clear()

        create_response = client.post(
            "/incidents",
            json={
                "source": "manual",
                "severity": "low",
                "environment": "dev",
                "namespace": "default",
                "workload": "test-app",
                "raw_alert": "test alert",
                "runbook_id": "rb-test",
            },
        )
        inc_id = create_response.json()["id"]

        with patch(
            "runguard.backend.ai.reasoner.AIReasoner.analyze",
            new_callable=AsyncMock,
            return_value=_ai_result(),
        ):
            analyze_response = client.post(f"/incidents/{inc_id}/analyze")
        assert analyze_response.status_code == 200
        assert _incidents[inc_id]["status"] in ("requires_approval", "resolved")
