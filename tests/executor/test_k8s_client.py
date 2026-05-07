from unittest.mock import MagicMock, patch

import pytest

from runguard.backend.executor.k8s_client import K8sClient


class TestK8sClient:
    @patch("runguard.backend.executor.k8s_client.client")
    @patch("runguard.backend.executor.k8s_client.config")
    def test_rollout_restart_calls_patch(self, mock_config, mock_client):
        mock_apps = MagicMock()
        mock_client.AppsV1Api.return_value = mock_apps
        k8s = K8sClient()
        k8s.rollout_restart("my-app", "default")
        mock_apps.patch_namespaced_deployment.assert_called_once()
        call_kwargs = mock_apps.patch_namespaced_deployment.call_args
        assert call_kwargs.kwargs["name"] == "my-app"
        assert call_kwargs.kwargs["namespace"] == "default"

    @patch("runguard.backend.executor.k8s_client.client")
    @patch("runguard.backend.executor.k8s_client.config")
    def test_scale_replicas_calls_patch(self, mock_config, mock_client):
        mock_apps = MagicMock()
        mock_client.AppsV1Api.return_value = mock_apps
        k8s = K8sClient()
        k8s.scale_replicas("my-app", 3, "default")
        mock_apps.patch_namespaced_deployment.assert_called_once()
        body = mock_apps.patch_namespaced_deployment.call_args.kwargs["body"]
        assert body["spec"]["replicas"] == 3

    @patch("runguard.backend.executor.k8s_client.client")
    @patch("runguard.backend.executor.k8s_client.config")
    def test_update_image_calls_patch(self, mock_config, mock_client):
        mock_apps = MagicMock()
        mock_deployment = MagicMock()
        mock_deployment.spec.template.spec.containers = [MagicMock(image="old:v1")]
        mock_apps.read_namespaced_deployment.return_value = mock_deployment
        mock_client.AppsV1Api.return_value = mock_apps
        k8s = K8sClient()
        k8s.update_image("my-app", "new:v2", "default")
        mock_apps.patch_namespaced_deployment.assert_called_once()

    @patch("runguard.backend.executor.k8s_client.client")
    @patch("runguard.backend.executor.k8s_client.config")
    def test_delete_pod_calls_delete(self, mock_config, mock_client):
        mock_core = MagicMock()
        mock_client.CoreV1Api.return_value = mock_core
        k8s = K8sClient()
        k8s.delete_pod("my-app-xxx", "default")
        mock_core.delete_namespaced_pod.assert_called_once_with(
            name="my-app-xxx", namespace="default"
        )

    @patch("runguard.backend.executor.k8s_client.client")
    @patch("runguard.backend.executor.k8s_client.config")
    def test_rollout_restart_handles_api_error(self, mock_config, mock_client):
        mock_apps = MagicMock()
        mock_apps.patch_namespaced_deployment.side_effect = Exception("API error")
        mock_client.AppsV1Api.return_value = mock_apps
        k8s = K8sClient()
        with pytest.raises(Exception, match="API error"):
            k8s.rollout_restart("my-app", "default")
