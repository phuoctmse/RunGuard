"""Tests for LLM-based incident planner."""

import json
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from runguard.backend.reasoning.planner import IncidentPlanner


SAMPLE_EVIDENCE = {
    "pod_logs": {"web-app-pod": "2024-01-01 ERROR Connection refused to database:5432"},
    "events": [{"reason": "BackOff", "message": "Back-off restarting failed container", "timestamp": "2024-01-01T00:00:00Z", "type": "Warning"}],
    "deployment_status": {"name": "web-app", "desired_replicas": 3, "ready_replicas": 1, "available_replicas": 1, "conditions": []},
}

SAMPLE_PLAN_RESPONSE = json.dumps({
    "summary": "Pod crash loop detected due to database connection failure",
    "root_causes": [
        {"cause": "Database service unreachable", "confidence": 0.85, "evidence_refs": ["web-app-pod logs"]},
        {"cause": "Database port misconfigured", "confidence": 0.4, "evidence_refs": ["pod logs show port 5432"]},
    ],
    "remediation_actions": [
        {"action": "fetch_logs", "target": "database-pod", "priority": 1, "reason": "Verify database pod status"},
        {"action": "rollout_restart", "target": "web-app", "priority": 2, "reason": "Restart after verifying database"},
    ],
})


@pytest.mark.asyncio
async def test_planner_generates_plan():
    planner = IncidentPlanner(api_key="test-key")
    with patch.object(planner.client.messages, "create", new_callable=AsyncMock) as mock_create:
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=SAMPLE_PLAN_RESPONSE)]
        mock_create.return_value = mock_response

        plan = await planner.generate_plan(
            incident_id="inc-001",
            alert_summary="Pod CrashLoopBackOff",
            evidence=SAMPLE_EVIDENCE,
            runbook_title="Pod CrashLoop Runbook",
        )
        assert plan["summary"] != ""
        assert len(plan["root_causes"]) == 2
        assert len(plan["remediation_actions"]) == 2


@pytest.mark.asyncio
async def test_planner_uses_structured_output():
    planner = IncidentPlanner(api_key="test-key")
    with patch.object(planner.client.messages, "create", new_callable=AsyncMock) as mock_create:
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=SAMPLE_PLAN_RESPONSE)]
        mock_create.return_value = mock_response

        await planner.generate_plan(
            incident_id="inc-001",
            alert_summary="Test alert",
            evidence=SAMPLE_EVIDENCE,
            runbook_title="Test",
        )
        call_args = mock_create.call_args
        assert call_args.kwargs["model"] == "claude-sonnet-4-20250514"


@pytest.mark.asyncio
async def test_planner_returns_empty_plan_on_error():
    planner = IncidentPlanner(api_key="test-key")
    with patch.object(planner.client.messages, "create", new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = Exception("API error")

        plan = await planner.generate_plan(
            incident_id="inc-001",
            alert_summary="Test",
            evidence=SAMPLE_EVIDENCE,
            runbook_title="Test",
        )
        assert plan["summary"] == ""
        assert plan["root_causes"] == []
