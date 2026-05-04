"""Tests for evidence aggregation collector."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from runguard.backend.evidence.collector import EvidenceCollector


@pytest.fixture
def mock_k8s():
    """Mock KubernetesEvidenceCollector."""
    with patch("runguard.backend.evidence.collector.KubernetesEvidenceCollector") as MockK8s:
        mock_instance = MagicMock()
        MockK8s.return_value = mock_instance
        yield mock_instance


@pytest.mark.asyncio
async def test_collect_success(mock_k8s):
    """Should return evidence with timeout=False on success."""
    mock_k8s.collect_all = AsyncMock(return_value={
        "pod_logs": {"pod-1": "logs"},
        "events": [{"reason": "BackOff"}],
        "deployment_status": {"name": "web-app"},
    })

    collector = EvidenceCollector(namespace="default", timeout_seconds=10)
    result = await collector.collect("web-app")

    assert result["timeout"] is False
    assert "pod-1" in result["pod_logs"]
    assert len(result["events"]) == 1


@pytest.mark.asyncio
async def test_collect_timeout(mock_k8s):
    """Should return empty evidence with timeout=True when timeout occurs."""
    async def slow_collect(workload):
        await asyncio.sleep(999)

    mock_k8s.collect_all = slow_collect

    collector = EvidenceCollector(namespace="default", timeout_seconds=0.1)
    result = await collector.collect("web-app")

    assert result["timeout"] is True
    assert result["timeout_seconds"] == 0.1
    assert result["pod_logs"] == {}
    assert result["events"] == []


@pytest.mark.asyncio
async def test_collect_passes_namespace(mock_k8s):
    """Should pass namespace to K8s collector."""
    mock_k8s.collect_all = AsyncMock(return_value={
        "pod_logs": {}, "events": [], "deployment_status": {},
    })

    collector = EvidenceCollector(namespace="staging", timeout_seconds=5)
    await collector.collect("api-server")

    mock_k8s.collect_all.assert_called_once_with("api-server")


@pytest.mark.asyncio
async def test_collect_default_timeout():
    """Default timeout should be 30 seconds."""
    with patch("runguard.backend.evidence.collector.KubernetesEvidenceCollector"):
        collector = EvidenceCollector()
        assert collector.timeout_seconds == 30
