import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from reasoner.fallback import FallbackClient


@pytest.mark.asyncio
async def test_fallback_to_raw_evidence():
    client = FallbackClient(primary_key="", bedrock_key="")

    result = await client.analyze(
        alert_name="TestAlert",
        namespace="default",
        evidence={"logs": "some logs"},
    )

    assert "evidence" in result
    assert result.get("source") == "raw_evidence"


@pytest.mark.asyncio
async def test_primary_client_called_first():
    mock_primary = AsyncMock()
    mock_primary.analyze_incident.return_value = {
        "root_cause": "OOMKill",
        "confidence": 0.9,
    }

    client = FallbackClient(
        primary_key="test-key",
        bedrock_key="",
        primary_client=mock_primary,
    )

    result = await client.analyze(
        alert_name="PodCrashLooping",
        namespace="production",
        evidence={"logs": "OOMKilled"},
    )

    assert result["root_cause"] == "OOMKill"
    mock_primary.analyze_incident.assert_called_once()


@pytest.mark.asyncio
async def test_primary_fails_falls_back_to_raw():
    mock_primary = AsyncMock()
    mock_primary.analyze_incident.side_effect = Exception("API down")

    client = FallbackClient(
        primary_key="test-key",
        bedrock_key="",
        primary_client=mock_primary,
    )

    result = await client.analyze(
        alert_name="TestAlert",
        namespace="default",
        evidence={"logs": "test"},
    )

    assert result.get("source") == "raw_evidence"