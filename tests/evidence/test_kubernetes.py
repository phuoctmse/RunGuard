"""Tests for Kubernetes evidence collector."""

from unittest.mock import MagicMock, patch
import pytest
from runguard.backend.evidence.kubernetes import KubernetesEvidenceCollector


@pytest.fixture
def mock_k8s_client():
    """Create a mock Kubernetes client."""
    with patch("runguard.backend.evidence.kubernetes.config") as mock_config:
        mock_config.load_kube_config = MagicMock()
        yield


@pytest.mark.asyncio
async def test_collect_pod_logs(mock_k8s_client):
    collector = KubernetesEvidenceCollector(namespace="default")
    collector.core_api = MagicMock()

    mock_pod = MagicMock()
    mock_pod.metadata.name = "test-pod"
    collector.core_api.list_namespaced_pod.return_value = MagicMock(items=[mock_pod])
    collector.core_api.read_namespaced_pod_log.return_value = "2024-01-01 ERROR connection refused"

    evidence = await collector.collect_pod_logs(workload="test-pod")
    assert "test-pod" in evidence
    assert "ERROR" in evidence["test-pod"]


@pytest.mark.asyncio
async def test_collect_events(mock_k8s_client):
    collector = KubernetesEvidenceCollector(namespace="default")
    collector.core_api = MagicMock()

    mock_event = MagicMock()
    mock_event.reason = "BackOff"
    mock_event.message = "Back-off restarting failed container"
    mock_event.last_timestamp.isoformat.return_value = "2024-01-01T00:00:00Z"
    mock_event.type = "Warning"
    collector.core_api.list_namespaced_event.return_value = MagicMock(items=[mock_event])

    events = await collector.collect_events(workload="test-pod")
    assert len(events) == 1
    assert events[0]["reason"] == "BackOff"


@pytest.mark.asyncio
async def test_collect_deployment_status(mock_k8s_client):
    collector = KubernetesEvidenceCollector(namespace="default")
    collector.apps_api = MagicMock()

    mock_deployment = MagicMock()
    mock_deployment.metadata.name = "web-app"
    mock_deployment.spec.replicas = 3
    mock_deployment.status.ready_replicas = 2
    mock_deployment.status.available_replicas = 2

    mock_condition = MagicMock()
    mock_condition.type = "Progressing"
    mock_condition.status = "True"
    mock_condition.reason = "NewReplicaSetAvailable"
    mock_condition.message = "ok"
    mock_deployment.status.conditions = [mock_condition]

    collector.apps_api.read_namespaced_deployment.return_value = mock_deployment

    status = await collector.collect_deployment_status(workload="web-app")
    assert status["name"] == "web-app"
    assert status["desired_replicas"] == 3
    assert status["ready_replicas"] == 2
