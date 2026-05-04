"""Tests for LLM planner — edge cases and _format_evidence."""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from runguard.backend.reasoning.planner import IncidentPlanner


def test_format_evidence_empty():
    """Should return 'No evidence collected' for empty evidence."""
    planner = IncidentPlanner(api_key="test")
    result = planner._format_evidence({})
    assert result == "No evidence collected"


def test_format_evidence_pod_logs_only():
    """Should format pod logs correctly."""
    planner = IncidentPlanner(api_key="test")
    evidence = {"pod_logs": {"pod-1": "ERROR line 1\nERROR line 2"}}
    result = planner._format_evidence(evidence)
    assert "Pod Logs (pod-1)" in result
    assert "ERROR line 1" in result


def test_format_evidence_truncates_long_logs():
    """Should truncate pod logs to 500 characters."""
    planner = IncidentPlanner(api_key="test")
    long_log = "x" * 1000
    evidence = {"pod_logs": {"pod-1": long_log}}
    result = planner._format_evidence(evidence)
    # The log part should be truncated to 500 chars
    assert "x" * 500 in result
    assert "x" * 501 not in result


def test_format_evidence_events_only():
    """Should format events correctly."""
    planner = IncidentPlanner(api_key="test")
    evidence = {
        "events": [
            {"reason": "BackOff", "message": "container crash"},
            {"reason": "Pulled", "message": "Image pulled"},
        ]
    }
    result = planner._format_evidence(evidence)
    assert "Event: BackOff - container crash" in result
    assert "Event: Pulled - Image pulled" in result


def test_format_evidence_events_limit_10():
    """Should limit events to first 10."""
    planner = IncidentPlanner(api_key="test")
    evidence = {"events": [{"reason": f"event-{i}", "message": "msg"} for i in range(20)]}
    result = planner._format_evidence(evidence)
    assert "Event: event-0" in result
    assert "Event: event-9" in result
    assert "Event: event-10" not in result


def test_format_evidence_deployment_status():
    """Should format deployment status correctly."""
    planner = IncidentPlanner(api_key="test")
    evidence = {
        "deployment_status": {
            "desired_replicas": 3,
            "ready_replicas": 1,
            "available_replicas": 1,
        }
    }
    result = planner._format_evidence(evidence)
    assert "desired=3" in result
    assert "ready=1" in result
    assert "available=1" in result


def test_format_evidence_event_missing_fields():
    """Should handle events with missing fields gracefully."""
    planner = IncidentPlanner(api_key="test")
    evidence = {"events": [{"reason": "BackOff"}]}
    result = planner._format_evidence(evidence)
    assert "Event: BackOff - " in result


def test_format_evidence_multiple_pod_logs():
    """Should format multiple pod logs."""
    planner = IncidentPlanner(api_key="test")
    evidence = {"pod_logs": {"pod-1": "logs-1", "pod-2": "logs-2"}}
    result = planner._format_evidence(evidence)
    assert "Pod Logs (pod-1)" in result
    assert "Pod Logs (pod-2)" in result


@pytest.mark.asyncio
async def test_planner_invalid_json_response():
    """Should return empty plan when LLM returns invalid JSON."""
    planner = IncidentPlanner(api_key="test")
    with patch.object(planner.client.messages, "create", new_callable=AsyncMock) as mock_create:
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="This is not JSON")]
        mock_create.return_value = mock_response

        plan = await planner.generate_plan(
            incident_id="inc-001",
            alert_summary="Test",
            evidence={},
            runbook_title="Test",
        )
        assert plan["summary"] == ""
        assert plan["root_causes"] == []


@pytest.mark.asyncio
async def test_planner_partial_json_response():
    """Should return empty plan when JSON is incomplete."""
    planner = IncidentPlanner(api_key="test")
    with patch.object(planner.client.messages, "create", new_callable=AsyncMock) as mock_create:
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"summary": "test"')]
        mock_create.return_value = mock_response

        plan = await planner.generate_plan(
            incident_id="inc-001",
            alert_summary="Test",
            evidence={},
        )
        assert plan["summary"] == ""


@pytest.mark.asyncio
async def test_planner_default_model():
    """Default model should be claude-sonnet-4-20250514."""
    planner = IncidentPlanner(api_key="test")
    assert planner.model == "claude-sonnet-4-20250514"


@pytest.mark.asyncio
async def test_planner_custom_model():
    """Should accept custom model."""
    planner = IncidentPlanner(api_key="test", model="claude-opus-4-20250514")
    assert planner.model == "claude-opus-4-20250514"


@pytest.mark.asyncio
async def test_planner_prompt_contains_evidence():
    """Prompt should include formatted evidence."""
    planner = IncidentPlanner(api_key="test")
    with patch.object(planner.client.messages, "create", new_callable=AsyncMock) as mock_create:
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"summary":"ok","root_causes":[],"remediation_actions":[]}')]
        mock_create.return_value = mock_response

        evidence = {"pod_logs": {"pod-1": "test-log-data"}}
        await planner.generate_plan(
            incident_id="inc-001",
            alert_summary="Test alert",
            evidence=evidence,
            runbook_title="Test Runbook",
        )

        call_args = mock_create.call_args
        prompt = call_args.kwargs["messages"][0]["content"]
        assert "inc-001" in prompt
        assert "Test alert" in prompt
        assert "Test Runbook" in prompt
        assert "test-log-data" in prompt
