"""Kubernetes evidence collector — gathers pod logs, events, deployment status."""

import asyncio
from kubernetes import client, config


class KubernetesEvidenceCollector:
    """Collects evidence from a Kubernetes cluster."""

    def __init__(self, namespace: str = "default", kubeconfig: str | None = None):
        self.namespace = namespace
        self.core_api: client.CoreV1Api | None = None
        self.apps_api: client.AppsV1Api | None = None
        self._load_config(kubeconfig)

    def _load_config(self, kubeconfig: str | None = None) -> None:
        """Load Kubernetes configuration."""
        try:
            if kubeconfig:
                config.load_kube_config(config_file=kubeconfig)
            else:
                config.load_kube_config()
        except Exception:
            config.load_incluster_config()

        self.core_api = client.CoreV1Api()
        self.apps_api = client.AppsV1Api()

    async def collect_pod_logs(self, workload: str, tail_lines: int = 100) -> dict:
        """Collect logs from pods matching the workload name."""
        evidence: dict = {}
        try:
            pods = self.core_api.list_namespaced_pod(
                namespace=self.namespace,
                label_selector=f"app={workload}",
            )
            for pod in pods.items:
                pod_name = pod.metadata.name
                try:
                    logs = self.core_api.read_namespaced_pod_log(
                        name=pod_name,
                        namespace=self.namespace,
                        tail_lines=tail_lines,
                    )
                    evidence[pod_name] = logs
                except Exception as e:
                    evidence[pod_name] = f"Error reading logs: {e}"
        except Exception as e:
            evidence["error"] = f"Failed to list pods: {e}"
        return evidence

    async def collect_events(self, workload: str) -> list:
        """Collect Kubernetes events related to the workload."""
        events = []
        try:
            event_list = self.core_api.list_namespaced_event(
                namespace=self.namespace,
                field_selector=f"involvedObject.name={workload}",
            )
            for event in event_list.items:
                events.append({
                    "reason": event.reason,
                    "message": event.message,
                    "timestamp": event.last_timestamp.isoformat() if event.last_timestamp else "",
                    "type": event.type,
                })
        except Exception as e:
            events.append({"reason": "Error", "message": str(e), "timestamp": "", "type": "Error"})
        return events

    async def collect_deployment_status(self, workload: str) -> dict:
        """Collect deployment status including replicas and conditions."""
        try:
            deployment = self.apps_api.read_namespaced_deployment(
                name=workload,
                namespace=self.namespace,
            )
            conditions = []
            if deployment.status.conditions:
                for cond in deployment.status.conditions:
                    conditions.append({
                        "type": cond.type,
                        "status": cond.status,
                        "reason": cond.reason,
                        "message": cond.message,
                    })
            return {
                "name": deployment.metadata.name,
                "desired_replicas": deployment.spec.replicas,
                "ready_replicas": deployment.status.ready_replicas or 0,
                "available_replicas": deployment.status.available_replicas or 0,
                "conditions": conditions,
            }
        except Exception as e:
            return {"error": f"Failed to get deployment: {e}"}

    async def collect_all(self, workload: str) -> dict:
        """Collect all available evidence for a workload."""
        logs, events, status = await asyncio.gather(
            self.collect_pod_logs(workload),
            self.collect_events(workload),
            self.collect_deployment_status(workload),
        )
        return {
            "pod_logs": logs,
            "events": events,
            "deployment_status": status,
        }
