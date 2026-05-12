from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from reasoner.llm import LLMClient


@pytest.mark.asyncio
async def test_analyze_incident_returns_structured_result():
    mock_response = MagicMock()
    mock_response.content = [
        MagicMock(
            text='{"root_cause": "OOMKill", "confidence": 0.92, "actions": ["increase_memory_limit"]}'
        )
    ]

    client = LLMClient(api_key="test-key", model="claude-sonnet-4-20250514")

    with patch.object(
        client.client.messages,
        "create",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        result = await client.analyze_incident(
            alert_name="PodCrashLooping",
            namespace="production",
            evidence={"logs": "OOMKilled"},
        )

    assert result["root_cause"] == "OOMKill"
    assert result["confidence"] == 0.92
    assert "increase_memory_limit" in result["actions"]


@pytest.mark.asyncio
async def test_analyze_incident_handles_invalid_json():
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="not valid json")]

    client = LLMClient(api_key="test-key", model="claude-sonnet-4-20250514")

    with patch.object(
        client.client.messages,
        "create",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        result = await client.analyze_incident(
            alert_name="TestAlert",
            namespace="default",
            evidence={},
        )

    assert "error" in result
