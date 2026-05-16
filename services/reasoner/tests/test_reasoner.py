import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from reasoner.orchestrator import ReasonerOrchestrator


@pytest.mark.asyncio
async def test_orchestrator_full_flow():
    mock_llm = AsyncMock()
    mock_llm.analyze_incident.return_value = {
        "root_cause": "OOMKill",
        "confidence": 0.92,
        "evidence_citations": ["OOMKilled"],
        "actions": ["increase_memory_limit"],
    }

    orch = ReasonerOrchestrator(llm=mock_llm)

    result = await orch.analyze(
        alert_name="PodCrashLooping",
        namespace="production",
        evidence={"logs": "OOMKilled"},
    )

    assert result.root_cause == "OOMKill"
    assert result.confidence == 0.92
    assert len(result.actions) > 0


@pytest.mark.asyncio
async def test_orchestrator_unmatched_runbook():
    mock_llm = AsyncMock()
    mock_llm.analyze_incident.return_value = {
        "root_cause": "unknown",
        "confidence": 0.1,
        "evidence_citations": [],
        "actions": [],
    }

    orch = ReasonerOrchestrator(llm=mock_llm, runbooks=[])

    result = await orch.analyze(
        alert_name="UnknownAlert",
        namespace="default",
        evidence={},
    )

    assert result.unmatched_runbook is True


@pytest.mark.asyncio
async def test_orchestrator_redacts_evidence():
    mock_llm = AsyncMock()
    mock_llm.analyze_incident.return_value = {
        "root_cause": "test",
        "confidence": 0.5,
        "evidence_citations": [],
        "actions": [],
    }

    orch = ReasonerOrchestrator(llm=mock_llm)

    await orch.analyze(
        alert_name="TestAlert",
        namespace="default",
        evidence={"logs": "API key sk-ant-1234567890abcdef"},
    )

    # Verify redacted evidence was sent to LLM
    call_args = mock_llm.analyze_incident.call_args
    sent_evidence = call_args.kwargs.get("evidence", {})
    assert "sk-ant-" not in sent_evidence.get("logs", "")