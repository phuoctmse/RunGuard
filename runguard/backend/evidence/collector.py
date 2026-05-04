"""Evidence aggregation with timeout support."""

import asyncio
from runguard.backend.evidence.kubernetes import KubernetesEvidenceCollector


class EvidenceCollector:
    """Aggregates evidence from multiple sources with a timeout."""

    def __init__(self, namespace: str = "default", timeout_seconds: int = 30):
        self.namespace = namespace
        self.timeout_seconds = timeout_seconds
        self.k8s_collector = KubernetesEvidenceCollector(namespace=namespace)

    async def collect(self, workload: str) -> dict:
        """Collect all evidence within the timeout."""
        try:
            evidence = await asyncio.wait_for(
                self.k8s_collector.collect_all(workload),
                timeout=self.timeout_seconds,
            )
            evidence["timeout"] = False
            return evidence
        except asyncio.TimeoutError:
            return {
                "pod_logs": {},
                "events": [],
                "deployment_status": {},
                "timeout": True,
                "timeout_seconds": self.timeout_seconds,
            }
