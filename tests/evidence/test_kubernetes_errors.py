"""Tests for Kubernetes evidence collector — error paths and edge cases."""

from unittest.mock import MagicMock, patch
import pytest
from runguard.backend.evidence.kubernetes import KubernetesEvidenceCollector


@pytest.fixture
def mock_k8s_client():
    """Create a mock Kubernetes client."""
    with patch("runguard.backend.evidence.kubernetes.config") as mock_config:
        mock_config.load_kube_config = MagicMock()
        yield


def test_init_with_kubeconfig(mock_k8s_client):
    """Should load config from specified kubeconfig path."""
    with patch("runguard.backend.evidence.kubernetes.config") as mock_config:
        collector = KubernetesEvidenceCollector(namespace="test", kubeconfig="/path/to/config")
        mock_config.load_kube_config.assert_called_with(config_file="/path/to/config")


def test_init_without_kubeconfig(mock_k8s_client):
    """Should load default kubeconfig when no path specified."""
    with patch("runguard.backend.evidence.kubernetes.config") as mock_config:
        collector = KubernetesEvidenceCollector(namespace="test")
        mock_config.load_kube_config.assert_called_with()


def test_init_fallback_to_incluster(mock_k8s_client):
    """Should fallback to incluster config when kubeconfig fails."""
    with patch("runguard.backend.evidence.kubernetes.config") as mock_config:
        mock_config.load_kube_config.side_effect = Exception("no kubeconfig")
        collector = KubernetesEvidenceCollector(namespace="test")
        mock_config.load_incluster_config.assert_called_once()


@pytest.mark.asyncio
async def test_collect_pod_logs_error_listing_pods(mock_k8s_client):
    """Should return error dict when listing pods fails."""
    collector = KubernetesEvidenceCollector(namespace="default")
    collector.core_api = MagicMock()
    collector.core_api.list_namespaced_pod.side_effect = Exception("API unavailable")

    result = await collector.collect_pod_logs(workload="web-app")
    assert "error" in result
    assert "Failed to list pods" in result["error"]


@pytest.mark.asyncio
async def test_collect_pod_logs_error_reading_single_pod(mock_k8s_client):
    """Should handle error for individual pod log read failure."""
    collector = KubernetesEvidenceCollector(namespace="default")
    collector.core_api = MagicMock()

    mock_pod = MagicMock()
    mock_pod.metadata.name = "bad-pod"
    collector.core_api.list_namespaced_pod.return_value = MagicMock(items=[mock_pod])
    collector.core_api.read_namespaced_pod_log.side_effect = Exception("pod not found")

    result = await collector.collect_pod_logs(workload="web-app")
    assert "bad-pod" in result
    assert "Error reading logs" in result["bad-pod"]


@pytest.mark.asyncio
async def test_collect_pod_logs_empty_pods(mock_k8s_client):
    """Should return empty dict when no pods found."""
    collector = KubernetesEvidenceCollector(namespace="default")
    collector.core_api = MagicMock()
    collector.core_api.list_namespaced_pod.return_value = MagicMock(items=[])

    result = await collector.collect_pod_logs(workload="nonexistent")
    assert result == {}


@pytest.mark.asyncio
async def test_collect_events_api_error(mock_k8s_client):
    """Should return error event when API call fails."""
    collector = KubernetesEvidenceCollector(namespace="default")
    collector.core_api = MagicMock()
    collector.core_api.list_namespaced_event.side_effect = Exception("forbidden")

    result = await collector.collect_events(workload="web-app")
    assert len(result) == 1
    assert result[0]["reason"] == "Error"
    assert result[0]["type"] == "Error"
    assert "forbidden" in result[0]["message"]


@pytest.mark.asyncio
async def test_collect_events_empty(mock_k8s_client):
    """Should return empty list when no events found."""
    collector = KubernetesEvidenceCollector(namespace="default")
    collector.core_api = MagicMock()
    collector.core_api.list_namespaced_event.return_value = MagicMock(items=[])

    result = await collector.collect_events(workload="web-app")
    assert result == []


@pytest.mark.asyncio
async def test_collect_events_no_timestamp(mock_k8s_client):
    """Should handle None last_timestamp gracefully."""
    collector = KubernetesEvidenceCollector(namespace="default")
    collector.core_api = MagicMock()

    mock_event = MagicMock()
    mock_event.reason = "Pulled"
    mock_event.message = "Image pulled"
    mock_event.last_timestamp = None
    mock_event.type = "Normal"
    collector.core_api.list_namespaced_event.return_value = MagicMock(items=[mock_event])

    result = await collector.collect_events(workload="web-app")
    assert result[0]["timestamp"] == ""


@pytest.mark.asyncio
async def test_collect_deployment_status_api_error(mock_k8s_client):
    """Should return error dict when deployment API fails."""
    collector = KubernetesEvidenceCollector(namespace="default")
    collector.apps_api = MagicMock()
    collector.apps_api.read_namespaced_deployment.side_effect = Exception("not found")

    result = await collector.collect_deployment_status(workload="missing-app")
    assert "error" in result
    assert "Failed to get deployment" in result["error"]


@pytest.mark.asyncio
async def test_collect_deployment_status_no_conditions(mock_k8s_client):
    """Should handle deployment with no conditions."""
    collector = KubernetesEvidenceCollector(namespace="default")
    collector.apps_api = MagicMock()

    mock_deployment = MagicMock()
    mock_deployment.metadata.name = "web-app"
    mock_deployment.spec.replicas = 1
    mock_deployment.status.ready_replicas = 1
    mock_deployment.status.available_replicas = 1
    mock_deployment.status.conditions = None
    collector.apps_api.read_namespaced_deployment.return_value = mock_deployment

    result = await collector.collect_deployment_status(workload="web-app")
    assert result["conditions"] == []


@pytest.mark.asyncio
async def test_collect_deployment_status_none_replicas(mock_k8s_client):
    """Should default to 0 when ready/available replicas is None."""
    collector = KubernetesEvidenceCollector(namespace="default")
    collector.apps_api = MagicMock()

    mock_deployment = MagicMock()
    mock_deployment.metadata.name = "web-app"
    mock_deployment.spec.replicas = 3
    mock_deployment.status.ready_replicas = None
    mock_deployment.status.available_replicas = None
    mock_deployment.status.conditions = []
    collector.apps_api.read_namespaced_deployment.return_value = mock_deployment

    result = await collector.collect_deployment_status(workload="web-app")
    assert result["ready_replicas"] == 0
    assert result["available_replicas"] == 0


@pytest.mark.asyncio
async def test_collect_all_aggregates(mock_k8s_client):
    """Should aggregate all evidence types."""
    collector = KubernetesEvidenceCollector(namespace="default")
    collector.core_api = MagicMock()
    collector.apps_api = MagicMock()

    # Mock pod logs
    mock_pod = MagicMock()
    mock_pod.metadata.name = "pod-1"
    collector.core_api.list_namespaced_pod.return_value = MagicMock(items=[mock_pod])
    collector.core_api.read_namespaced_pod_log.return_value = "logs"

    # Mock events
    collector.core_api.list_namespaced_event.return_value = MagicMock(items=[])

    # Mock deployment
    mock_deployment = MagicMock()
    mock_deployment.metadata.name = "web-app"
    mock_deployment.spec.replicas = 1
    mock_deployment.status.ready_replicas = 1
    mock_deployment.status.available_replicas = 1
    mock_deployment.status.conditions = []
    collector.apps_api.read_namespaced_deployment.return_value = mock_deployment

    result = await collector.collect_all("web-app")
    assert "pod_logs" in result
    assert "events" in result
    assert "deployment_status" in result
