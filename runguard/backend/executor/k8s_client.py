from datetime import UTC, datetime

from kubernetes import client, config


class K8sClient:
    """Wrapper around Kubernetes API for executing remediation actions."""

    def __init__(self, kubeconfig: str | None = None):
        try:
            if kubeconfig:
                config.load_kube_config(config_file=kubeconfig)
            else:
                config.load_kube_config()
        except Exception:
            config.load_incluster_config()

        self.apps_api = client.AppsV1Api()
        self.core_api = client.CoreV1Api()

    def rollout_restart(self, name: str, namespace: str = "default") -> dict:
        """Trigger a rollout restart by patching deployment annotation."""
        body = {
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "kubectl.kubernetes.io/restartedAt": (
                                datetime.now(UTC).isoformat()
                            )
                        }
                    }
                }
            }
        }
        self.apps_api.patch_namespaced_deployment(
            name=name, namespace=namespace, body=body
        )
        return {"action": "rollout_restart", "target": name, "namespace": namespace}

    def scale_replicas(
        self, name: str, replicas: int, namespace: str = "default"
    ) -> dict:
        """Scale a deployment to the specified number of replicas."""
        body = {"spec": {"replicas": replicas}}
        self.apps_api.patch_namespaced_deployment(
            name=name, namespace=namespace, body=body
        )
        return {
            "action": "scale_replicas",
            "target": name,
            "replicas": replicas,
            "namespace": namespace,
        }

    def update_image(
        self,
        name: str,
        image: str,
        namespace: str = "default",
        container_index: int = 0,
    ) -> dict:
        """Update container image for a deployment."""
        deployment = self.apps_api.read_namespaced_deployment(
            name=name, namespace=namespace
        )
        containers = deployment.spec.template.spec.containers
        if container_index >= len(containers):
            raise ValueError(
                f"Container index {container_index} out of range "
                f"(deployment has {len(containers)} containers)"
            )
        old_image = containers[container_index].image
        body = {
            "spec": {
                "template": {
                    "spec": {
                        "containers": [
                            {"name": containers[container_index].name, "image": image}
                        ]
                    }
                }
            }
        }
        self.apps_api.patch_namespaced_deployment(
            name=name, namespace=namespace, body=body
        )
        return {
            "action": "update_image",
            "target": name,
            "old_image": old_image,
            "new_image": image,
            "namespace": namespace,
        }

    def delete_pod(self, name: str, namespace: str = "default") -> dict:
        """Delete a specific pod."""
        self.core_api.delete_namespaced_pod(name=name, namespace=namespace)
        return {"action": "delete_pod", "target": name, "namespace": namespace}
