"""Tests for AIReasoner Claude API integration."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from runguard.backend.ai.reasoner import AIReasoner


@pytest.fixture
def mock_anthropic_response():
    """Create a mock Claude API response."""
    result = {
        "summary": "Pod CrashLoopBackOff caused by OOMKilled",
        "root_causes": [
            {
                "cause": "Container memory limit too low",
                "confidence": 0.92,
                "evidence": ["Pod logs show OOMKilled", "Memory limit 128Mi"],
            }
        ],
        "actions": [
            {
                "name": "rollout_restart",
                "target": "my-app",
                "parameters": {},
                "reason": "Restart to apply new config",
            }
        ],
    }
    block = MagicMock()
    block.text = json.dumps(result)
    response = MagicMock()
    response.content = [block]
    return response


@pytest.fixture
def reasoner():
    """Create an AIReasoner with a fake API key."""
    with patch("runguard.backend.ai.reasoner.anthropic.AsyncAnthropic") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        reasoner = AIReasoner(api_key="test-key", model="test-model")
        yield reasoner


@pytest.mark.asyncio
async def test_analyze_returns_structured_result(reasoner, mock_anthropic_response):
    """Mock API and verify summary/root_causes/actions are returned."""
    reasoner.client.messages.create = AsyncMock(return_value=mock_anthropic_response)

    result = await reasoner.analyze(
        incident_id="inc-001",
        namespace="default",
        workload="my-app",
        severity="critical",
        raw_alert="Pod CrashLoopBackOff",
        evidence={"pod_logs": {"my-app-abc": "OOMKilled"}},
        runbook_title="Restart Workload",
    )

    assert result["summary"] == "Pod CrashLoopBackOff caused by OOMKilled"
    assert len(result["root_causes"]) == 1
    assert result["root_causes"][0]["cause"] == "Container memory limit too low"
    assert result["root_causes"][0]["confidence"] == 0.92
    assert len(result["actions"]) == 1
    assert result["actions"][0]["name"] == "rollout_restart"


@pytest.mark.asyncio
async def test_analyze_calls_claude_with_correct_model(reasoner, mock_anthropic_response):
    """Verify the model parameter is passed to the Claude API."""
    reasoner.client.messages.create = AsyncMock(return_value=mock_anthropic_response)

    await reasoner.analyze(
        incident_id="inc-002",
        namespace="default",
        workload="my-app",
        severity="high",
        raw_alert="High CPU",
        evidence={},
    )

    reasoner.client.messages.create.assert_called_once()
    call_kwargs = reasoner.client.messages.create.call_args[1]
    assert call_kwargs["model"] == "test-model"


@pytest.mark.asyncio
async def test_analyze_returns_empty_on_api_error(reasoner):
    """Mock API exception and verify empty result structure."""
    reasoner.client.messages.create = AsyncMock(side_effect=Exception("API error"))

    result = await reasoner.analyze(
        incident_id="inc-003",
        namespace="default",
        workload="my-app",
        severity="high",
        raw_alert="Service down",
        evidence={},
    )

    assert result["summary"] == ""
    assert result["root_causes"] == []
    assert result["actions"] == []


@pytest.mark.asyncio
async def test_analyze_returns_empty_on_invalid_json(reasoner):
    """Mock bad JSON response and verify empty result structure."""
    block = MagicMock()
    block.text = "not valid json {{{"
    response = MagicMock()
    response.content = [block]
    reasoner.client.messages.create = AsyncMock(return_value=response)

    result = await reasoner.analyze(
        incident_id="inc-004",
        namespace="default",
        workload="my-app",
        severity="medium",
        raw_alert="Slow response",
        evidence={},
    )

    assert result["summary"] == ""
    assert result["root_causes"] == []
    assert result["actions"] == []


@pytest.mark.asyncio
async def test_analyze_uses_runbook_title(reasoner, mock_anthropic_response):
    """Verify runbook_title appears in the prompt sent to Claude."""
    reasoner.client.messages.create = AsyncMock(return_value=mock_anthropic_response)

    await reasoner.analyze(
        incident_id="inc-005",
        namespace="default",
        workload="my-app",
        severity="critical",
        raw_alert="CrashLoopBackOff",
        evidence={},
        runbook_title="Restart Workload",
    )

    call_kwargs = reasoner.client.messages.create.call_args[1]
    user_message = call_kwargs["messages"][0]["content"]
    assert "Restart Workload" in user_message
