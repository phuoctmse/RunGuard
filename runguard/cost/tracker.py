"""Cost tracker — AWS Cost Explorer and OpenCost integration."""

from datetime import UTC, datetime, timedelta

import boto3
import httpx

from runguard.cost.models import (
    ActionCostEstimate,
    CostEntry,
    CostSource,
    IncidentCostSummary,
    NamespaceCost,
)

# Estimated costs per action type (USD, rough estimates)
ACTION_COST_ESTIMATES: dict[str, float] = {
    "rollout_restart": 0.01,
    "scale_deployment": 0.05,
    "fetch_logs": 0.005,
    "ssm_trigger": 0.03,
    "cloudwatch_metrics": 0.01,
    "k8s_pod_logs": 0.005,
    "k8s_events": 0.005,
    "k8s_deployment_status": 0.002,
    "k8s_describe_pod": 0.002,
}


class CostTracker:
    """Tracks and estimates costs for incidents and remediation actions."""

    def __init__(
        self,
        region: str = "us-east-1",
        opencost_endpoint: str = "",
    ) -> None:
        self.region = region
        self.opencost_endpoint = opencost_endpoint.rstrip("/")

    def get_incident_cost(
        self,
        incident_id: str,
        namespace: str = "",
        hours: int = 24,
    ) -> IncidentCostSummary:
        """Get cost data for an incident's time window.

        Queries AWS Cost Explorer for infrastructure costs during
        the incident period.

        Args:
            incident_id: The incident to get costs for
            namespace: K8s namespace (for filtering)
            hours: How many hours back to query

        Returns:
            IncidentCostSummary with cost breakdown
        """
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(hours=hours)

        entries = self._query_cost_explorer(start_time, end_time, namespace)

        return IncidentCostSummary(
            incident_id=incident_id,
            total_cost=sum(e.amount for e in entries),
            cost_entries=entries,
        )

    def get_namespace_cost(self, namespace: str, hours: int = 24) -> NamespaceCost:
        """Get namespace-level cost from OpenCost/Kubecost.

        Args:
            namespace: Kubernetes namespace
            hours: How many hours back to query

        Returns:
            NamespaceCost with CPU, memory, storage breakdown
        """
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(hours=hours)

        if self.opencost_endpoint:
            return self._query_opencost(namespace, start_time, end_time)

        # Return estimated costs when OpenCost is not configured
        return NamespaceCost(
            namespace=namespace,
            cpu_cost=0.0,
            memory_cost=0.0,
            storage_cost=0.0,
            total_cost=0.0,
            period_start=start_time,
            period_end=end_time,
        )

    def estimate_action_cost(self, action_name: str) -> ActionCostEstimate:
        """Estimate the cost impact of a proposed action.

        Args:
            action_name: The action to estimate (e.g. rollout_restart)

        Returns:
            ActionCostEstimate with estimated cost and confidence
        """
        estimated = ACTION_COST_ESTIMATES.get(action_name, 0.01)
        return ActionCostEstimate(
            action_name=action_name,
            estimated_cost=estimated,
            confidence=0.5,
            description=f"Estimated cost for {action_name}",
        )

    def get_cost_summary(
        self,
        incident_id: str,
        namespace: str,
        action_names: list[str],
        hours: int = 24,
    ) -> IncidentCostSummary:
        """Get a combined cost summary for an incident.

        Combines infrastructure costs with action cost estimates.

        Args:
            incident_id: The incident ID
            namespace: K8s namespace
            action_names: List of proposed action names
            hours: Hours to look back

        Returns:
            IncidentCostSummary with all cost data
        """
        incident_cost = self.get_incident_cost(incident_id, namespace, hours)
        namespace_costs = [self.get_namespace_cost(namespace, hours)]
        action_estimates = [self.estimate_action_cost(a) for a in action_names]

        incident_cost.namespace_costs = namespace_costs
        incident_cost.estimated_action_cost = sum(
            e.estimated_cost for e in action_estimates
        )
        return incident_cost

    def _query_cost_explorer(
        self,
        start_time: datetime,
        end_time: datetime,
        namespace: str = "",
    ) -> list[CostEntry]:
        """Query AWS Cost Explorer for cost data."""
        try:
            ce = boto3.client("ce", region_name=self.region)
            response = ce.get_cost_and_usage(
                TimePeriod={
                    "Start": start_time.strftime("%Y-%m-%d"),
                    "End": end_time.strftime("%Y-%m-%d"),
                },
                Granularity="DAILY",
                Metrics=["UnblendedCost"],
                GroupBy=[
                    {"Type": "DIMENSION", "Key": "SERVICE"},
                ],
            )
            entries: list[CostEntry] = []
            for result in response.get("ResultsByTime", []):
                for group in result.get("Groups", []):
                    service = group["Keys"][0] if group["Keys"] else "Unknown"
                    amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
                    entries.append(
                        CostEntry(
                            source=CostSource.AWS_COST_EXPLORER,
                            amount=amount,
                            period_start=start_time,
                            period_end=end_time,
                            namespace=namespace,
                            description=service,
                        )
                    )
            return entries
        except Exception:
            return []

    def _query_opencost(
        self,
        namespace: str,
        start_time: datetime,
        end_time: datetime,
    ) -> NamespaceCost:
        """Query OpenCost/Kubecost API for namespace-level costs."""
        try:
            url = (
                f"{self.opencost_endpoint}/allocation"
                f"?window={start_time.isoformat()},{end_time.isoformat()}"
                f"&accumulate=true"
                f"&filter=namespace:{namespace}"
            )
            response = httpx.get(url, timeout=10.0)
            response.raise_for_status()
            data = response.json()

            # Parse OpenCost response
            allocations = data.get("data", [{}])
            if allocations:
                ns_data = allocations[0].get(namespace, {})
                return NamespaceCost(
                    namespace=namespace,
                    cpu_cost=ns_data.get("cpuCost", 0.0),
                    memory_cost=ns_data.get("ramCost", 0.0),
                    storage_cost=ns_data.get("pvCost", 0.0),
                    total_cost=ns_data.get("totalCost", 0.0),
                    period_start=start_time,
                    period_end=end_time,
                )
        except Exception:
            pass

        return NamespaceCost(
            namespace=namespace,
            period_start=start_time,
            period_end=end_time,
        )
